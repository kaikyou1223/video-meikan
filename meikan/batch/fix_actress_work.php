<?php
/**
 * actress_work誤紐付け修正バッチ
 *
 * FANZA APIの出演者リストを照合し、実際に出演していない作品の紐付けを削除する。
 * 対象: 指定された女優、または全女優（引数なしの場合）
 *
 * Usage:
 *   php batch/fix_actress_work.php              # 全女優（作品数が多い順）
 *   php batch/fix_actress_work.php nia           # slug指定
 *   php batch/fix_actress_work.php --dry-run     # 削除せずカウントのみ
 *   php batch/fix_actress_work.php nia --dry-run
 */

require_once __DIR__ . '/config.php';

$apiId = getenv('FANZA_API_ID');
$affiliateId = getenv('FANZA_AFFILIATE_ID');

if (!$apiId || !$affiliateId) {
    batchLog('ERROR: FANZA API credentials not set');
    exit(1);
}

$db = Database::getInstance();

// 引数解析
$targetSlug = null;
$dryRun = false;
foreach (array_slice($argv, 1) as $arg) {
    if ($arg === '--dry-run') {
        $dryRun = true;
    } else {
        $targetSlug = $arg;
    }
}

/**
 * 女優名が一致するか判定（括弧内の別名も照合）
 */
function actressNameMatches(string $apiName, string $dbName): bool
{
    if ($apiName === $dbName) return true;

    if (preg_match('/^(.+?)\s*（(.+?)）$/', $apiName, $m)) {
        $mainName = trim($m[1]);
        if ($mainName === $dbName) return true;

        $aliases = preg_split('/[、,]\s*/', $m[2]);
        foreach ($aliases as $alias) {
            if (trim($alias) === $dbName) return true;
        }
    }
    return false;
}

// 対象女優を取得
if ($targetSlug) {
    $stmt = $db->prepare('SELECT a.id, a.name, a.slug, COUNT(aw.work_id) as work_count FROM actresses a JOIN actress_work aw ON a.id = aw.actress_id WHERE a.slug = ? GROUP BY a.id');
    $stmt->execute([$targetSlug]);
    $actresses = $stmt->fetchAll();
    if (empty($actresses)) {
        batchLog("ERROR: Actress '{$targetSlug}' not found or has no works");
        exit(1);
    }
} else {
    $actresses = $db->query('SELECT a.id, a.name, a.slug, COUNT(aw.work_id) as work_count FROM actresses a JOIN actress_work aw ON a.id = aw.actress_id GROUP BY a.id ORDER BY work_count DESC')->fetchAll();
}

$modeLabel = $dryRun ? '[DRY RUN] ' : '';
batchLog("{$modeLabel}対象女優: " . count($actresses) . "名");

foreach ($actresses as $actress) {
    $actressId = $actress['id'];
    $actressName = $actress['name'];
    $currentCount = $actress['work_count'];

    // FANZA APIで女優名を検索し、実際に出演している作品のsource_idを収集
    $validSourceIds = [];
    $offset = 1;

    while (true) {
        $params = http_build_query([
            'api_id' => $apiId,
            'affiliate_id' => $affiliateId,
            'site' => 'FANZA',
            'service' => 'digital',
            'floor' => 'videoa',
            'hits' => 100,
            'sort' => 'date',
            'keyword' => $actressName,
            'offset' => $offset,
            'output' => 'json',
        ]);

        $url = 'https://api.dmm.com/affiliate/v3/ItemList?' . $params;
        $response = @file_get_contents($url);

        if ($response === false) {
            batchLog("  API エラー (offset={$offset}) - スキップ");
            break;
        }

        $data = json_decode($response, true);
        if (empty($data['result']['items'])) break;

        $items = $data['result']['items'];
        $totalCount = $data['result']['total_count'] ?? 0;

        foreach ($items as $item) {
            $sourceId = $item['content_id'] ?? ($item['product_id'] ?? '');
            if (!$sourceId) continue;

            // 出演者リストに対象女優が含まれるか確認
            if (!empty($item['iteminfo']['actress'])) {
                foreach ($item['iteminfo']['actress'] as $actressInfo) {
                    if (actressNameMatches($actressInfo['name'] ?? '', $actressName)) {
                        $validSourceIds[$sourceId] = true;
                        break;
                    }
                }
            }
        }

        $offset += count($items);
        if ($offset > $totalCount) break;

        usleep(500000);
    }

    $validCount = count($validSourceIds);

    if ($validCount === 0) {
        batchLog("  {$actressName} ({$actress['slug']}): API結果0件 - スキップ（手動確認が必要）");
        continue;
    }

    // 現在のDB紐付けと比較
    if ($validCount >= $currentCount) {
        batchLog("  {$actressName} ({$actress['slug']}): {$currentCount}件 → 問題なし");
        continue;
    }

    $removeCount = $currentCount - $validCount;
    batchLog("{$modeLabel}{$actressName} ({$actress['slug']}): {$currentCount}件 → {$validCount}件 （{$removeCount}件削除）");

    if (!$dryRun) {
        // 有効なwork_idを取得
        if (!empty($validSourceIds)) {
            $placeholders = implode(',', array_fill(0, count($validSourceIds), '?'));
            $stmt = $db->prepare("SELECT id FROM works WHERE source = 'fanza' AND source_id IN ({$placeholders})");
            $stmt->execute(array_keys($validSourceIds));
            $validWorkIds = $stmt->fetchAll(PDO::FETCH_COLUMN);

            if (!empty($validWorkIds)) {
                $wphs = implode(',', array_fill(0, count($validWorkIds), '?'));
                $stmt = $db->prepare("DELETE FROM actress_work WHERE actress_id = ? AND work_id NOT IN ({$wphs})");
                $stmt->execute(array_merge([$actressId], $validWorkIds));
                batchLog("  削除完了: {$stmt->rowCount()}件");
            }
        }
    }

    usleep(500000);
}

batchLog("{$modeLabel}修正処理完了");

if (!$dryRun) {
    Cache::clear();
    batchLog("キャッシュクリア完了");
}

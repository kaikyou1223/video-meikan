<?php
/**
 * actress_work紐付けバリデーション
 *
 * ランダムに女優を選び、DBの紐付けとFANZA APIの出演者リストを照合する。
 * 誤紐付けが見つかった場合は非ゼロで終了する。
 *
 * Usage: php batch/validate_actress_works.php [--count=10] [--samples=5]
 *   --count   チェックする女優数（デフォルト: 10）
 *   --samples 各女優からサンプリングする作品数（デフォルト: 5）
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
$actressCount = 10;
$samplesPerActress = 5;
foreach (array_slice($argv, 1) as $arg) {
    if (preg_match('/^--count=(\d+)$/', $arg, $m)) $actressCount = (int)$m[1];
    if (preg_match('/^--samples=(\d+)$/', $arg, $m)) $samplesPerActress = (int)$m[1];
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

// ランダムに女優を選択（作品が1件以上ある女優のみ）
$stmt = $db->prepare('
    SELECT a.id, a.name, a.slug, COUNT(aw.work_id) as work_count
    FROM actresses a
    JOIN actress_work aw ON a.id = aw.actress_id
    GROUP BY a.id
    HAVING work_count > 0
    ORDER BY RAND()
    LIMIT ?
');
$stmt->execute([$actressCount]);
$actresses = $stmt->fetchAll();

batchLog("=== actress_work バリデーション ===");
batchLog("チェック対象: {$actressCount}名 × {$samplesPerActress}作品サンプル");

$totalChecked = 0;
$totalErrors = 0;
$errorDetails = [];

foreach ($actresses as $actress) {
    // ランダムに作品をサンプリング
    $stmt = $db->prepare('
        SELECT w.source_id, w.title
        FROM works w
        JOIN actress_work aw ON w.id = aw.work_id
        WHERE aw.actress_id = ? AND w.source = ?
        ORDER BY RAND()
        LIMIT ?
    ');
    $stmt->execute([$actress['id'], 'fanza', $samplesPerActress]);
    $works = $stmt->fetchAll();

    $errors = 0;

    foreach ($works as $work) {
        // FANZA APIで作品情報を取得
        $params = http_build_query([
            'api_id' => $apiId,
            'affiliate_id' => $affiliateId,
            'site' => 'FANZA',
            'service' => 'digital',
            'floor' => 'videoa',
            'hits' => 1,
            'cid' => $work['source_id'],
            'output' => 'json',
        ]);

        $url = 'https://api.dmm.com/affiliate/v3/ItemList?' . $params;
        $response = @file_get_contents($url);

        if ($response === false) {
            batchLog("  API error for CID: {$work['source_id']}");
            usleep(300000);
            continue;
        }

        $data = json_decode($response, true);
        $items = $data['result']['items'] ?? [];

        if (empty($items)) {
            // 作品がAPIから消えている場合はスキップ
            usleep(300000);
            continue;
        }

        $item = $items[0];
        $found = false;

        if (!empty($item['iteminfo']['actress'])) {
            foreach ($item['iteminfo']['actress'] as $actressInfo) {
                if (actressNameMatches($actressInfo['name'] ?? '', $actress['name'])) {
                    $found = true;
                    break;
                }
            }
        }

        $totalChecked++;
        if (!$found) {
            $errors++;
            $totalErrors++;
            $errorDetails[] = "{$actress['name']}({$actress['slug']}) ↔ {$work['source_id']}";
        }

        usleep(300000);
    }

    $status = $errors > 0 ? "✗ {$errors}件の誤紐付け" : '✓ OK';
    batchLog("  {$actress['name']} ({$actress['slug']}): {$actress['work_count']}作品中{$samplesPerActress}件チェック → {$status}");
}

batchLog("--- 結果 ---");
batchLog("チェック: {$totalChecked}件, 誤紐付け: {$totalErrors}件");

if ($totalErrors > 0) {
    batchLog("誤紐付け一覧:");
    foreach ($errorDetails as $detail) {
        batchLog("  ✗ {$detail}");
    }
    batchLog("ERROR: 誤紐付けが検出されました。fix_actress_work.php の実行を検討してください。");
    exit(1);
}

batchLog("全件OK — 誤紐付けは検出されませんでした。");
exit(0);

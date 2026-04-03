<?php
/**
 * 作品数が膨張している女優を検出するスクリプト
 *
 * FANZA APIのキーワード検索total_countとDB件数を比較し、
 * DBの方がAPI結果に近い（=キーワード検索のヒット数≒DB件数）女優を検出する。
 * これらはキーワード検索結果を無条件で紐付けた可能性が高い。
 *
 * Usage: php batch/check_inflated_actresses.php [--threshold=500]
 */

require_once __DIR__ . '/config.php';

$apiId = getenv('FANZA_API_ID');
$affiliateId = getenv('FANZA_AFFILIATE_ID');

if (!$apiId || !$affiliateId) {
    batchLog('ERROR: FANZA API credentials not set');
    exit(1);
}

$db = Database::getInstance();

// 閾値: DB作品数がこれ以上の女優のみチェック
$threshold = 500;
foreach (array_slice($argv, 1) as $arg) {
    if (preg_match('/^--threshold=(\d+)$/', $arg, $m)) {
        $threshold = (int)$m[1];
    }
}

// DB作品数が閾値以上の女優を取得
$stmt = $db->prepare('
    SELECT a.id, a.name, a.slug, COUNT(aw.work_id) as db_count
    FROM actresses a
    JOIN actress_work aw ON a.id = aw.actress_id
    GROUP BY a.id
    HAVING db_count >= ?
    ORDER BY db_count DESC
');
$stmt->execute([$threshold]);
$actresses = $stmt->fetchAll();

batchLog("チェック対象: " . count($actresses) . "名（DB作品数 >= {$threshold}）");

$results = [];

foreach ($actresses as $actress) {
    // FANZA APIでキーワード検索のtotal_countを取得（1件だけ取得すればOK）
    $params = http_build_query([
        'api_id' => $apiId,
        'affiliate_id' => $affiliateId,
        'site' => 'FANZA',
        'service' => 'digital',
        'floor' => 'videoa',
        'hits' => 1,
        'keyword' => $actress['name'],
        'offset' => 1,
        'output' => 'json',
    ]);

    $url = 'https://api.dmm.com/affiliate/v3/ItemList?' . $params;
    $response = @file_get_contents($url);

    if ($response === false) {
        batchLog("  API error: {$actress['name']}");
        usleep(500000);
        continue;
    }

    $data = json_decode($response, true);
    $apiTotal = $data['result']['total_count'] ?? 0;
    $dbCount = $actress['db_count'];

    // DB件数がAPIキーワード検索結果の80%以上 = 膨張の可能性大
    // （正常なら、キーワード検索結果 >> 実際の出演作品数）
    $ratio = $apiTotal > 0 ? round($dbCount / $apiTotal * 100) : 0;

    $flag = '';
    if ($ratio >= 70) {
        $flag = ' ★要修正';
    } elseif ($ratio >= 50) {
        $flag = ' ▲要確認';
    }

    if ($flag) {
        batchLog(sprintf("  %s (%s): DB=%d, API検索=%d, 比率=%d%%%s",
            $actress['name'], $actress['slug'], $dbCount, $apiTotal, $ratio, $flag));
    }

    $results[] = [
        'slug' => $actress['slug'],
        'name' => $actress['name'],
        'db_count' => $dbCount,
        'api_total' => $apiTotal,
        'ratio' => $ratio,
        'flag' => trim($flag),
    ];

    usleep(300000);
}

// サマリー
$needsFix = array_filter($results, fn($r) => $r['ratio'] >= 70);
$needsCheck = array_filter($results, fn($r) => $r['ratio'] >= 50 && $r['ratio'] < 70);

batchLog("=== サマリー ===");
batchLog("★要修正（比率70%+）: " . count($needsFix) . "名");
batchLog("▲要確認（比率50-69%）: " . count($needsCheck) . "名");

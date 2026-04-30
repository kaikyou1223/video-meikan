<?php
/**
 * FANZA 価格情報 更新専用バッチ
 *
 * fetch_fanza.php の UPDATE 部分のみを抽出した軽量版。
 * 新規作品の発見・女優紐付け・ジャンル紐付け・サンプル画像保存は行わず、
 * 既に DB に存在する作品の price / list_price / rental_price /
 * rental_list_price / sale_end_at / campaign_title だけを更新する。
 *
 * 想定実行頻度: 毎日 1 回（FANZA セールが数日単位で切り替わるため）
 *
 * Usage: php batch/update_prices.php
 */

require_once __DIR__ . '/config.php';

$apiId = getenv('FANZA_API_ID');
$affiliateId = getenv('FANZA_AFFILIATE_ID');

if (!$apiId || !$affiliateId) {
    batchLog('ERROR: FANZA_API_ID / FANZA_AFFILIATE_ID が設定されていません');
    exit(1);
}

$db = Database::getInstance();

$actresses = $db->query('SELECT id, name FROM actresses ORDER BY id')->fetchAll();
batchLog('対象女優: ' . count($actresses) . '名');

$totalUpdated = 0;
$totalSkipped = 0;
$apiErrors = 0;

foreach ($actresses as $actress) {
    $offset = 1;
    $updatedForActress = 0;

    while (true) {
        $params = http_build_query([
            'api_id' => $apiId,
            'affiliate_id' => $affiliateId,
            'site' => 'FANZA',
            'service' => 'digital',
            'floor' => 'videoa',
            'hits' => 100,
            'sort' => 'date',
            'keyword' => $actress['name'],
            'offset' => $offset,
            'output' => 'json',
        ]);

        $url = 'https://api.dmm.com/affiliate/v3/ItemList?' . $params;
        $response = @file_get_contents($url);

        if ($response === false) {
            batchLog("  API エラー: {$actress['name']} (offset={$offset})");
            $apiErrors++;
            break;
        }

        $data = json_decode($response, true);
        if (empty($data['result']['items'])) {
            break;
        }

        $items = $data['result']['items'];
        $totalCount = $data['result']['total_count'] ?? 0;

        foreach ($items as $item) {
            $sourceId = $item['content_id'] ?? ($item['product_id'] ?? '');
            if (!$sourceId) continue;

            $existing = $db->prepare('SELECT id FROM works WHERE source = ? AND source_id = ?');
            $existing->execute(['fanza', $sourceId]);
            $workId = $existing->fetchColumn();

            if (!$workId) {
                $totalSkipped++;
                continue;
            }

            $price = null;
            $listPrice = null;
            $rentalPrice = null;
            $rentalListPrice = null;
            if (!empty($item['prices'])) {
                $deliveries = $item['prices']['deliveries']['delivery'] ?? [];
                foreach ($deliveries as $d) {
                    $type = $d['type'] ?? '';
                    $dPrice = (int)preg_replace('/[^0-9]/', '', $d['price'] ?? '0');
                    $dListPrice = (int)preg_replace('/[^0-9]/', '', $d['list_price'] ?? '0') ?: $dPrice;
                    if ($type === 'download' && $dPrice > 0) {
                        $price = $dPrice;
                        $listPrice = $dListPrice;
                    }
                    if ($dPrice > 0 && ($rentalPrice === null || $dPrice < $rentalPrice)) {
                        $rentalPrice = $dPrice;
                        $rentalListPrice = $dListPrice;
                    }
                }
                if ($price === null && isset($item['prices']['price'])) {
                    $price = (int)preg_replace('/[^0-9]/', '', $item['prices']['price']);
                    $listPrice = (int)preg_replace('/[^0-9]/', '', $item['prices']['list_price'] ?? '');
                }
            }

            $saleEndAt = null;
            $campaignTitle = null;
            if (!empty($item['campaign'])) {
                $campaign = $item['campaign'][0] ?? $item['campaign'];
                $saleEndAt = !empty($campaign['date_end']) ? date('Y-m-d H:i:s', strtotime($campaign['date_end'])) : null;
                $campaignTitle = $campaign['title'] ?? null;
            }

            $db->prepare('UPDATE works SET price = ?, list_price = ?, sale_end_at = ?, campaign_title = ?, rental_price = ?, rental_list_price = ?, price_updated_at = NOW() WHERE id = ?')
               ->execute([$price, $listPrice, $saleEndAt, $campaignTitle, $rentalPrice, $rentalListPrice, $workId]);
            $totalUpdated++;
            $updatedForActress++;
        }

        $offset += count($items);
        if ($offset > $totalCount) break;

        usleep(500000); // 0.5 秒
    }

    if ($updatedForActress > 0) {
        batchLog("  {$actress['name']}: {$updatedForActress} 件更新");
    }
}

batchLog("=== 完了 ===");
batchLog("更新: {$totalUpdated} 件 / 未登録スキップ: {$totalSkipped} 件 / API エラー: {$apiErrors} 件");

// セール表示の鮮度を保つためキャッシュもクリア
Cache::clear();
batchLog('キャッシュクリア完了');

if ($apiErrors > 0) {
    exit(2); // API エラーがあった場合は非ゼロで終了 → Slack 通知対象に
}

<?php
/**
 * デビュー日算出バッチ
 * 各女優の最古の作品リリース日をdebut_dateとして設定する
 *
 * Usage: php batch/calculate_debut_dates.php
 */

require_once __DIR__ . '/config.php';

batchLog('=== デビュー日算出 開始 ===');

$db = Database::getInstance();

// 作品が紐付いている女優のdebut_dateを一括更新
$stmt = $db->exec("
    UPDATE actresses a
    INNER JOIN (
        SELECT aw.actress_id, MIN(w.release_date) AS debut_date
        FROM actress_work aw
        INNER JOIN works w ON aw.work_id = w.id
        WHERE w.release_date IS NOT NULL
        GROUP BY aw.actress_id
    ) sub ON a.id = sub.actress_id
    SET a.debut_date = sub.debut_date
");

batchLog("更新件数: {$stmt} 件");

// 結果確認
$result = $db->query("
    SELECT COUNT(*) AS total,
           COUNT(debut_date) AS with_debut,
           MIN(debut_date) AS earliest,
           MAX(debut_date) AS latest
    FROM actresses
")->fetch(PDO::FETCH_ASSOC);

batchLog("全女優: {$result['total']} 名, debut_date設定済: {$result['with_debut']} 名");
batchLog("デビュー日範囲: {$result['earliest']} 〜 {$result['latest']}");

// キャッシュクリア
Cache::clear();
batchLog('キャッシュクリア完了');

batchLog('=== デビュー日算出 完了 ===');

<?php
/**
 * 女優スラグ修正バッチ
 * newcomers_kanji_fix.json を読み込み、既存女優のスラグを更新する。
 * DBに未登録の女優は新規登録する。
 *
 * Usage: php batch/fix_actress_slugs.php [JSONファイルパス]
 */

require_once __DIR__ . '/config.php';

$jsonPath = $argv[1] ?? __DIR__ . '/data/newcomers_kanji_fix.json';
if (!file_exists($jsonPath)) {
    batchLog("ERROR: {$jsonPath} が見つかりません");
    exit(1);
}

$entries = json_decode(file_get_contents($jsonPath), true);
if (!$entries) {
    batchLog("ERROR: JSONの読み込みに失敗しました");
    exit(1);
}

batchLog("=== 女優スラグ修正バッチ開始 ===");
batchLog("修正対象: " . count($entries) . " 名");

$db = Database::getInstance();

// 既存のslugを取得（重複チェック用）
$existingSlugs = $db->query('SELECT slug FROM actresses')->fetchAll(PDO::FETCH_COLUMN);
$slugSet = array_flip($existingSlugs);

$updateStmt = $db->prepare('UPDATE actresses SET slug = ? WHERE name = ? AND slug != ?');
$insertStmt = $db->prepare('INSERT IGNORE INTO actresses (name, slug) VALUES (?, ?)');

$updated = 0;
$inserted = 0;
$skipped = 0;
$errors = [];
$redirects = []; // 旧slug → 新slug のリダイレクトマップ

// 既存のリダイレクトマップがあれば読み込む
$redirectFile = ROOT_DIR . '/config/slug_redirects.php';
if (file_exists($redirectFile)) {
    $redirects = require $redirectFile;
}

foreach ($entries as $entry) {
    $name = $entry['name'] ?? '';
    $newSlug = $entry['slug'] ?? '';

    if (!$name || !$newSlug) {
        $errors[] = "不正なエントリ: " . json_encode($entry, JSON_UNESCAPED_UNICODE);
        continue;
    }

    // スラグ形式チェック
    if (!preg_match('/^[a-z0-9][a-z0-9-]*$/', $newSlug)) {
        $errors[] = "{$name}: 不正なスラグ形式 '{$newSlug}'";
        continue;
    }

    // 名前でDBを検索
    $stmt = $db->prepare('SELECT id, slug FROM actresses WHERE name = ?');
    $stmt->execute([$name]);
    $actress = $stmt->fetch(PDO::FETCH_ASSOC);

    if ($actress) {
        // 既存女優 — スラグが異なる場合のみ更新
        if ($actress['slug'] === $newSlug) {
            $skipped++;
            continue;
        }

        // 新しいスラグが他の女優に使われていないかチェック
        if (isset($slugSet[$newSlug])) {
            $errors[] = "{$name}: スラグ '{$newSlug}' は既に使用中";
            continue;
        }

        $oldSlug = $actress['slug'];
        $updateStmt->execute([$newSlug, $name, $newSlug]);
        if ($updateStmt->rowCount() > 0) {
            // slugSetを更新
            unset($slugSet[$oldSlug]);
            $slugSet[$newSlug] = true;
            // リダイレクトマップに追加
            $redirects[$oldSlug] = $newSlug;
            $updated++;
            batchLog("更新: {$name} ({$oldSlug} → {$newSlug})");
        } else {
            $skipped++;
        }
    } else {
        // 未登録女優 — 新規登録
        if (isset($slugSet[$newSlug])) {
            $errors[] = "{$name}: スラグ '{$newSlug}' は既に使用中（新規登録失敗）";
            continue;
        }

        $insertStmt->execute([$name, $newSlug]);
        if ($insertStmt->rowCount() > 0) {
            $slugSet[$newSlug] = true;
            $inserted++;
            batchLog("新規登録: {$name} (slug: {$newSlug})");
        } else {
            $errors[] = "{$name}: INSERT失敗";
        }
    }
}

batchLog("完了: 更新 {$updated} 名, 新規登録 {$inserted} 名, スキップ {$skipped} 名");
if ($errors) {
    batchLog("エラー: " . implode(', ', $errors));
}

// リダイレクトマップを保存
if ($redirects) {
    $export = "<?php\nreturn " . var_export($redirects, true) . ";\n";
    file_put_contents($redirectFile, $export);
    batchLog("リダイレクトマップ保存: " . count($redirects) . " 件 ({$redirectFile})");
}

// キャッシュクリア
Cache::clear();
batchLog("キャッシュクリア完了");
batchLog("=== 女優スラグ修正バッチ終了 ===");

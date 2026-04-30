<?php
/**
 * 作品グリッド内の挿入ロジック（共通）
 *
 * 入力:
 *   $globalIndex   現在の作品の通し番号（1始まり）
 *   $insertionMode 'actress' | 'genre'
 *   $actress       (両モード共通)
 *   $similarActresses   ('actress'モード or 'genre'モードでフォールバック使用時)
 *   $otherGenres        ('genre'モードのみ。[{slug,name,work_count,thumbnail_url}, ...])
 *
 * 挿入ルール:
 *   index 5      → 関連カード（actress: similar / genre: other-genres）※1回限り
 *   index 9,13,17... (4件おき) → 広告
 */

if (($globalIndex - 9) >= 0 && ($globalIndex - 9) % 4 === 0) {
    $adNum = (($globalIndex - 9) / 4) + 1;
    $adSize = 'infeed';
    $adLabel = "インフィード広告 #{$adNum}";
    // バナー始まりで交互（odd=banner / even=widget）
    $adType = ($adNum % 2 === 1) ? 'banner' : 'widget';
    // 1番目（globalIndex 9）は即時、それ以降は viewport 接近時に遅延ロード
    $adLazy = ($adNum > 1);
    require __DIR__ . '/ad-slot.php';
    return;
}

if ($globalIndex === 5) {
    if (($insertionMode ?? 'actress') === 'genre' && !empty($otherGenres)) {
        require __DIR__ . '/other-genres-inline.php';
        return;
    }
    if (!empty($similarActresses)) {
        require __DIR__ . '/similar-actresses-inline.php';
        return;
    }
}

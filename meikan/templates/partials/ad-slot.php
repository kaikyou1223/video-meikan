<?php
$adSize = $adSize ?? 'responsive';
$adType = $adType ?? 'banner'; // 'banner' | 'widget'
$affiliateId = 'avhakase2026-001';

// FANZA 広告ユニット
$units = [
    'banner' => [
        '300x250' => '1911_300_250',
        '728x90'  => '1911_728_90',
    ],
    'widget' => [
        '300x250' => '23d78fdfcec2455468c01405cc1961bd',
        '728x90'  => 'd23d1f3f02fdf8e317f8311e2232e711',
    ],
];

$renderUnit = function (string $type, string $size) use ($units, $affiliateId): void {
    $id = $units[$type][$size] ?? '';
    if (!$id) return;
    if ($type === 'banner') {
        ?>
        <ins class="widget-banner"></ins><script class="widget-banner-script" src="https://widget-view.dmm.co.jp/js/banner_placement.js?affiliate_id=<?= h($affiliateId) ?>&banner_id=<?= h($id) ?>"></script>
        <?php
    } else {
        ?>
        <ins class="dmm-widget-placement" data-id="<?= h($id) ?>" style="background:transparent"></ins><script src="https://widget-view.dmm.co.jp/js/placement.js" class="dmm-widget-scripts" data-id="<?= h($id) ?>"></script>
        <?php
    }
};
?>
<div class="ad-slot ad-slot--<?= h($adSize) ?>" data-size="<?= h($adSize) ?>" data-type="<?= h($adType) ?>">
    <?php if ($adSize === 'bottom'): ?>
        <div class="ad-slot__inner ad-slot__inner--sp"><?php $renderUnit($adType, '300x250'); ?></div>
        <div class="ad-slot__inner ad-slot__inner--pc"><?php $renderUnit($adType, '728x90'); ?></div>
    <?php else: ?>
        <div class="ad-slot__inner"><?php $renderUnit($adType, '300x250'); ?></div>
    <?php endif; ?>
</div>

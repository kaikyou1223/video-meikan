<div class="similar-inline">
    <p class="similar-inline__title"><?= h($actress['name']) ?>が好きな人にオススメ</p>
    <div class="similar-inline__scroll">
        <?php foreach ($similarActresses as $similar): ?>
            <a href="<?= h(url($similar['slug'] . '/')) ?>" class="similar-inline__item">
                <div class="similar-inline__image">
                    <?php if (!empty($similar['thumbnail_url'])): ?>
                        <img src="<?= h($similar['thumbnail_url']) ?>" alt="<?= h($similar['name']) ?>" width="300" height="300" loading="lazy">
                    <?php else: ?>
                        <div class="similar-inline__placeholder"></div>
                    <?php endif; ?>
                </div>
                <span class="similar-inline__name"><?= h($similar['name']) ?><?php if (!empty($similar['birthday'])): ?><span class="similar-inline__age">（<?= (new DateTime($similar['birthday']))->diff(new DateTime())->y ?>歳）</span><?php endif; ?></span>
                <?php if (!empty($similar['bust']) && !empty($similar['waist']) && !empty($similar['hip'])): ?>
                    <span class="similar-inline__size">B<?= (int)$similar['bust'] ?> W<?= (int)$similar['waist'] ?> H<?= (int)$similar['hip'] ?></span>
                <?php endif; ?>
            </a>
        <?php endforeach; ?>
    </div>
</div>

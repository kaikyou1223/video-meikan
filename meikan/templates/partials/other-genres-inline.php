<div class="other-genres-inline">
    <p class="other-genres-inline__title"><?= h($actress['name']) ?>の他のジャンル</p>
    <div class="other-genres-inline__scroll">
        <?php foreach ($otherGenres as $og): ?>
            <a href="<?= h(url($actress['slug'] . '/' . $og['slug'] . '/')) ?>" class="other-genres-inline__card">
                <div class="other-genres-inline__image">
                    <?php if (!empty($og['cover_image'])): ?>
                        <img src="<?= h($og['cover_image']) ?>" alt="<?= h($og['name']) ?>" loading="lazy">
                    <?php else: ?>
                        <div class="other-genres-inline__placeholder"></div>
                    <?php endif; ?>
                </div>
                <div class="other-genres-inline__body">
                    <span class="other-genres-inline__name"><?= h($og['name']) ?></span>
                    <span class="other-genres-inline__count"><?= (int)$og['work_count'] ?>本</span>
                </div>
            </a>
        <?php endforeach; ?>
    </div>
</div>

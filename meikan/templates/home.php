<h1 class="page-title"><?= h(SITE_NAME) ?></h1>
<p class="page-description"><?= h(SITE_DESCRIPTION) ?></p>

<?php $headingText = 'ピックアップ女優'; require TEMPLATE_DIR . '/partials/section-heading.php'; ?>
<div class="actress-grid">
    <?php foreach ($pickupActresses as $actress): ?>
        <?php require TEMPLATE_DIR . '/partials/actress-card.php'; ?>
    <?php endforeach; ?>
</div>
<p class="home-more"><a href="<?= url('meikan/') ?>" class="home-more__link">女優名鑑をもっと見る &rarr;</a></p>

<?php $headingText = '最新記事'; require TEMPLATE_DIR . '/partials/section-heading.php'; ?>
<div class="article-list">
    <?php foreach ($latestArticles as $article): ?>
    <a href="<?= h(url('article/' . $article['slug'] . '/')) ?>" class="article-list-card">
        <div class="article-list-card__body">
            <?php if (!empty($article['category'])): ?>
            <span class="article-list-card__category"><?= h($article['category']) ?></span>
            <?php endif; ?>
            <h2 class="article-list-card__title"><?= h($article['title']) ?></h2>
            <p class="article-list-card__desc"><?= h($article['description']) ?></p>
            <time class="article-list-card__date"><?= h($article['published_at']) ?></time>
        </div>
    </a>
    <?php endforeach; ?>
</div>
<p class="home-more"><a href="<?= url('article/') ?>" class="home-more__link">記事一覧をもっと見る &rarr;</a></p>

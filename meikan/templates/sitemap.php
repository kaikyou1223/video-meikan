<?= '<?xml version="1.0" encoding="UTF-8"?>' . PHP_EOL ?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
<?php foreach ($urls as $u): ?>
    <url>
        <loc><?= h($u['loc']) ?></loc>
<?php if (!empty($u['lastmod'])): ?>
        <lastmod><?= h($u['lastmod']) ?></lastmod>
<?php endif; ?>
        <changefreq><?= h($u['changefreq']) ?></changefreq>
        <priority><?= h($u['priority']) ?></priority>
<?php if (!empty($u['images'])): ?>
<?php foreach ($u['images'] as $img): ?>
        <image:image>
            <image:loc><?= h($img['loc']) ?></image:loc>
<?php if (!empty($img['title'])): ?>
            <image:title><?= h($img['title']) ?></image:title>
<?php endif; ?>
        </image:image>
<?php endforeach; ?>
<?php endif; ?>
    </url>
<?php endforeach; ?>
</urlset>

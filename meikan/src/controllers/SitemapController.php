<?php

class SitemapController
{
    public function index(array $params): void
    {
        header('Content-Type: application/xml; charset=UTF-8');

        $actresses = Actress::allForSitemap();
        $urls = [];

        // TOP
        $urls[] = [
            'loc' => fullUrl(),
            'changefreq' => 'daily',
            'priority' => '1.0',
        ];

        // 名鑑TOP
        $urls[] = [
            'loc' => fullUrl('meikan/'),
            'changefreq' => 'daily',
            'priority' => '0.9',
        ];

        // 記事一覧
        $urls[] = [
            'loc' => fullUrl('article/'),
            'changefreq' => 'weekly',
            'priority' => '0.8',
        ];

        // 個別記事（noindex除外）
        $articles = ArticleController::allArticles();
        foreach ($articles as $article) {
            if (!empty($article['noindex'])) continue;
            $urlEntry = [
                'loc' => fullUrl('article/' . $article['slug'] . '/'),
                'changefreq' => 'monthly',
                'priority' => '0.7',
            ];
            if (!empty($article['updated_at'])) {
                $urlEntry['lastmod'] = $article['updated_at'];
            } elseif (!empty($article['published_at'])) {
                $urlEntry['lastmod'] = $article['published_at'];
            }
            $urls[] = $urlEntry;
        }

        // 女優ページ + ジャンルページ
        foreach ($actresses as $actress) {
            $urlEntry = [
                'loc' => fullUrl($actress['slug'] . '/'),
                'lastmod' => date('Y-m-d', strtotime($actress['updated_at'])),
                'changefreq' => 'weekly',
                'priority' => '0.8',
            ];
            if (!empty($actress['thumbnail_url'])) {
                $urlEntry['images'] = [
                    ['loc' => $actress['thumbnail_url'], 'title' => $actress['name']],
                ];
            }
            $urls[] = $urlEntry;

            // 作品数が少ない女優はジャンルページを生成しない
            $actressObj = Actress::findBySlug($actress['slug']);
            if ($actressObj && (int)$actressObj['work_count'] > ACTRESS_WORK_THRESHOLD) {
                $genreSlugs = Genre::allSlugsForActress($actressObj['id']);
                foreach ($genreSlugs as $genreSlug) {
                    $urls[] = [
                        'loc' => fullUrl($actress['slug'] . '/' . $genreSlug . '/'),
                        'changefreq' => 'weekly',
                        'priority' => '0.6',
                    ];
                }
            }
        }

        render('sitemap', [
            'noLayout' => true,
            'urls' => $urls,
        ]);
    }
}

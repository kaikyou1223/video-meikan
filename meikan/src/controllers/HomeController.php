<?php

class HomeController
{
    /** ジャンル別セクションの定義（記事と対応） */
    private const GENRE_SECTIONS = [
        [
            'genre_slug' => 'chijo',
            'title' => '痴女ジャンルのおすすめ女優',
            'article_slug' => 'chijo-osusume',
        ],
        [
            'genre_slug' => 'kyonyu',
            'title' => '巨乳ジャンルのおすすめ女優',
            'article_slug' => 'shinjin-av-bakunyu',
        ],
    ];

    public function index(array $params): void
    {
        // 最新デビュー月の新人女優
        $latestMonth = Actress::getLatestDebutMonth();
        $debutActresses = [];
        $debutMonthLabel = '';
        if ($latestMonth) {
            $debutActresses = Actress::findByDebutMonth($latestMonth);
            $debutActresses = array_values(array_filter($debutActresses, function ($a) {
                return !empty($a['thumbnail_url'])
                    && strpos($a['thumbnail_url'], '/digital/video/') === false
                    && strpos($a['thumbnail_url'], 'now_printing') === false;
            }));
            $debutActresses = array_slice($debutActresses, 0, 6);
            $parts = explode('-', $latestMonth);
            $debutMonthLabel = (int)$parts[0] . '年' . (int)$parts[1] . '月';
        }

        // ジャンル別おすすめ女優
        $genreSections = [];
        foreach (self::GENRE_SECTIONS as $section) {
            $genreActresses = Actress::findTopByGenre($section['genre_slug'], 6);
            $genreSections[] = [
                'title' => $section['title'],
                'article_slug' => $section['article_slug'],
                'actresses' => $genreActresses,
            ];
        }

        $debutArticleSlug = $latestMonth
            ? 'shinjin-av-' . $latestMonth
            : null;

        // 最新記事5件
        $articles = ArticleController::allArticles();
        $latestArticles = array_slice($articles, 0, 5);

        $jsonLd = [
            '@context' => 'https://schema.org',
            '@type' => 'Organization',
            'name' => SITE_NAME,
            'url' => fullUrl(),
            'description' => SITE_DESCRIPTION,
        ];

        render('home', [
            'pageTitle' => SITE_NAME . ' | ' . SITE_DESCRIPTION,
            'metaDescription' => SITE_DESCRIPTION,
            'jsonLd' => $jsonLd,
            'debutActresses' => $debutActresses,
            'debutMonthLabel' => $debutMonthLabel,
            'debutArticleSlug' => $debutArticleSlug,
            'genreSections' => $genreSections,
            'latestArticles' => $latestArticles,
        ]);
    }
}

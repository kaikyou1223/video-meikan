<?php

class ActressController
{
    public function show(array $params): void
    {
        $actress = Actress::findBySlug($params['actress_slug']);
        if (!$actress) {
            http_response_code(404);
            render('404', ['pageTitle' => 'ページが見つかりません | ' . SITE_NAME]);
            return;
        }

        $workCount = (int)$actress['work_count'];
        $isFewWorks = $workCount <= ACTRESS_WORK_THRESHOLD;

        // 作品数が少ない場合はジャンル取得をスキップ
        $genres = [];
        if (!$isFewWorks) {
            $genres = Actress::getGenres($actress['id']);
        }

        $similarActresses = Actress::getSimilarActresses($actress['id']);

        // 似ている女優が空の場合、タグ+デビュー時期ベースの関連女優をフォールバック
        // さらに関連女優も空なら逆引き（他女優のsimilar/relatedに含まれている）
        $relatedActresses = [];
        if (empty($similarActresses)) {
            $relatedActresses = Actress::getRelatedActresses($actress['id']);
            if (empty($relatedActresses)) {
                $relatedActresses = Actress::getReverseLookupActresses($actress['id']);
            }
        }

        // 作品一覧を表示（デフォルト: 単体作品のみ・人気順）
        $worksPage = currentPage();
        $totalWorks = Work::countSingleByActress($actress['id']);
        $worksPagination = paginate($totalWorks, ITEMS_PER_PAGE, $worksPage);
        $works = Work::findByActressPaginated($actress['id'], ITEMS_PER_PAGE, $worksPagination['offset']);

        // サンプル画像を一括取得
        $workIds = array_column($works, 'id');
        $workSampleImages = Work::getSampleImagesBulk($workIds);

        // Person スキーマ
        $person = [
            '@type' => 'Person',
            'name' => $actress['name'],
            'url' => fullUrl($actress['slug'] . '/'),
        ];
        if (!empty($actress['thumbnail_url'])) {
            $person['image'] = $actress['thumbnail_url'];
        }
        if (!empty($actress['birthday'])) {
            $person['birthDate'] = $actress['birthday'];
        }
        if (!empty($actress['height'])) {
            $person['height'] = [
                '@type' => 'QuantitativeValue',
                'value' => (int)$actress['height'],
                'unitCode' => 'CMT',
            ];
        }

        // ItemList スキーマ
        $itemList = [
            '@type' => 'ItemList',
            'name' => $actress['name'] . 'のジャンル別作品',
            'numberOfItems' => count($genres) ?: count($works),
            'itemListElement' => [],
        ];

        if (!empty($genres)) {
            foreach ($genres as $i => $genre) {
                $itemList['itemListElement'][] = [
                    '@type' => 'ListItem',
                    'position' => $i + 1,
                    'name' => $genre['name'],
                    'url' => fullUrl($actress['slug'] . '/' . $genre['slug'] . '/'),
                ];
            }
        } else {
            foreach ($works as $i => $work) {
                $product = [
                    '@type' => 'Product',
                    'name' => $work['title'],
                    'sku' => $work['source_id'],
                ];
                if (!empty($work['thumbnail_url'])) {
                    $product['image'] = $work['thumbnail_url'];
                }
                if (!empty($work['affiliate_url'])) {
                    $product['offers'] = [
                        '@type' => 'Offer',
                        'url' => $work['affiliate_url'],
                        'priceCurrency' => 'JPY',
                        'availability' => 'https://schema.org/InStock',
                    ];
                }
                if (!empty($work['review_average']) && !empty($work['review_count'])) {
                    $product['aggregateRating'] = [
                        '@type' => 'AggregateRating',
                        'ratingValue' => round((float)$work['review_average'], 2),
                        'reviewCount' => (int)$work['review_count'],
                    ];
                }
                $itemList['itemListElement'][] = [
                    '@type' => 'ListItem',
                    'position' => $i + 1,
                    'item' => $product,
                ];
            }
        }

        $jsonLd = [
            '@context' => 'https://schema.org',
            '@graph' => [$person, $itemList],
        ];

        $metaName = $actress['name'];
        $metaWorkCount = $workCount;
        $metaAgePart = '';
        if (!empty($actress['birthday'])) {
            $metaAge = (new DateTime($actress['birthday']))->diff(new DateTime())->y;
            $metaAgePart = "（{$metaAge}歳）";
        }
        $metaSizePart = '';
        if (!empty($actress['bust']) && !empty($actress['waist']) && !empty($actress['hip'])) {
            $metaSizePart = "B{$actress['bust']}/W{$actress['waist']}/H{$actress['hip']}。";
        }
        $metaYear = date('Y');
        $metaDescription = "{$metaName}{$metaAgePart}の最新AV作品{$metaWorkCount}本をジャンル別に検索できる。{$metaSizePart}評価順・新着順での並べ替えにも対応。{$metaYear}年の最新作品を随時更新中。";

        render('actress', [
            'pageTitle' => $actress['name'] . 'のジャンル別作品一覧 | ' . SITE_NAME,
            'metaDescription' => $metaDescription,
            'breadcrumbs' => [
                ['label' => 'TOP', 'url' => ''],
                ['label' => $actress['name'], 'url' => ''],
            ],
            'actress' => $actress,
            'genres' => $genres,
            'works' => $works,
            'workSampleImages' => $workSampleImages,
            'totalWorks' => $totalWorks,
            'worksPagination' => $worksPagination,
            'isFewWorks' => $isFewWorks,
            'similarActresses' => $similarActresses,
            'relatedActresses' => $relatedActresses,
            'jsonLd' => $jsonLd,
        ]);
    }
}

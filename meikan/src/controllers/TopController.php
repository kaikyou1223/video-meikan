<?php

class TopController
{
    private const PER_PAGE = 60;

    public function index(array $params): void
    {
        $page       = currentPage();
        $total      = Actress::count();
        $pagination = paginate($total, self::PER_PAGE, $page);
        $all        = Actress::all();
        $actresses  = array_slice($all, $pagination['offset'], self::PER_PAGE);

        render('top', [
            'pageTitle'       => SITE_TITLE . ' | ' . SITE_NAME,
            'metaDescription' => 'AV女優' . $total . '人をジャンル別に検索できる名鑑。巨乳・痴女・素人など多数のジャンルから好みの作品を探せます。',
            'breadcrumbs'     => [
                ['label' => 'TOP', 'url' => ''],
                ['label' => '名鑑TOP', 'url' => ''],
            ],
            'actresses'  => $actresses,
            'pagination' => $pagination,
        ]);
    }
}

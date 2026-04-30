<?php

class ApiController
{
    public function works(array $params): void
    {
        header('Content-Type: application/json; charset=utf-8');

        $actressId = (int)($_GET['actress_id'] ?? 0);
        $genreId = (int)($_GET['genre_id'] ?? 0);

        if (!$actressId) {
            http_response_code(400);
            echo json_encode(['error' => 'actress_id is required']);
            return;
        }

        $page = max(1, (int)($_GET['page'] ?? 1));
        $sort = $_GET['sort'] ?? '';
        $query = trim($_GET['q'] ?? '');
        $singleOnly = ($_GET['single'] ?? '0') === '1';
        $vrFilter = $_GET['vr'] ?? '';

        // バリデーション
        if (!in_array($sort, ['', 'rank', 'review', '-date'], true)) {
            $sort = '';
        }
        if (!in_array($vrFilter, ['', '2d', 'vr'], true)) {
            $vrFilter = '';
        }

        if ($genreId) {
            // ジャンル指定あり（ジャンルページ）
            $total = Work::searchCount($actressId, $genreId, $query, $singleOnly, $vrFilter);
            $totalPages = max(1, (int)ceil($total / ITEMS_PER_PAGE));
            $page = min($page, $totalPages);
            $offset = ($page - 1) * ITEMS_PER_PAGE;
            $works = Work::search($actressId, $genreId, $sort, $query, $singleOnly, $vrFilter, ITEMS_PER_PAGE, $offset);
        } else {
            // ジャンル指定なし（女優ページ）
            $total = Work::searchCountByActress($actressId, $query, $singleOnly, $vrFilter);
            $totalPages = max(1, (int)ceil($total / ITEMS_PER_PAGE));
            $page = min($page, $totalPages);
            $offset = ($page - 1) * ITEMS_PER_PAGE;
            $works = Work::searchByActress($actressId, $sort, $query, $singleOnly, $vrFilter, ITEMS_PER_PAGE, $offset);
        }

        // サンプル画像を一括取得
        $workIds = array_column($works, 'id');
        $workSampleImages = Work::getSampleImagesBulk($workIds);

        // 挿入ヘルパー用コンテキスト
        $actress = Actress::findById($actressId);
        $insertionMode = $genreId ? 'genre' : 'actress';
        $similarActresses = [];
        $otherGenres = [];
        if ($insertionMode === 'genre' && $actress) {
            $allGenres = Actress::getGenres((int)$actress['id']);
            $candidates = array_values(array_filter($allGenres, fn($g) => (int)$g['id'] !== $genreId));
            if ($candidates) {
                $coverIds = array_map(fn($g) => (int)$g['id'], $candidates);
                $covers = Genre::getCoverImagesForActress((int)$actress['id'], $coverIds);
                foreach ($candidates as $g) {
                    $g['cover_image'] = $covers[(int)$g['id']] ?? '';
                    $otherGenres[] = $g;
                }
            }
        } elseif ($insertionMode === 'actress' && $actress) {
            $similars = Actress::getSimilarActresses((int)$actress['id']);
            $similarActresses = !empty($similars) ? $similars : Actress::getRelatedActresses((int)$actress['id']);
        }

        // work-card-v2 + 挿入ヘルパーでHTML生成
        $worksOffset = $offset;
        $workIndex = $worksOffset;
        ob_start();
        foreach ($works as $work) {
            require TEMPLATE_DIR . '/partials/work-card-v2.php';
            $workIndex++;
            $globalIndex = $workIndex;
            require TEMPLATE_DIR . '/partials/work-list-insertions.php';
        }
        $html = ob_get_clean();

        echo json_encode([
            'html' => $html,
            'total' => $total,
            'total_pages' => $totalPages,
            'page' => $page,
        ], JSON_UNESCAPED_UNICODE);
    }
}

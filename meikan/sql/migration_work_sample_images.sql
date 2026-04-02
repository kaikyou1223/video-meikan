-- サンプル画像テーブル追加
CREATE TABLE IF NOT EXISTS work_sample_images (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    work_id INT UNSIGNED NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    sort_order TINYINT UNSIGNED NOT NULL DEFAULT 0,
    INDEX idx_work_id (work_id),
    FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

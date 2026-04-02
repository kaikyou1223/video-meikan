-- サンプル動画URLカラム追加
ALTER TABLE works ADD COLUMN sample_movie_url VARCHAR(500) DEFAULT NULL AFTER review_average;

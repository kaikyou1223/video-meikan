-- debut_date カラムを actresses テーブルに追加
ALTER TABLE actresses
    ADD COLUMN debut_date DATE DEFAULT NULL AFTER thumbnail_url;

CREATE INDEX idx_debut_date ON actresses (debut_date);

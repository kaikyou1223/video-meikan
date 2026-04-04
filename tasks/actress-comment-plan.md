# 女優コメント全件生成 実施計画

## 概要

本番998人の女優全員に「AV博士コメント」を生成・保存する。
コメントはWebSearch付きリサーチで高品質な内容を担保する。

---

## 現状

| 環境 | 女優数 | commentカラム |
|------|--------|--------------|
| ローカル | 217人 | あり（10人が保有） |
| 本番 | 998人 | **なし（未マイグレーション）** |

- テンプレート（actress.php）はコメント表示対応済み（未デプロイ）
- migration_add_actress_profile.sql にcommentカラム追加が含まれているが本番未適用

---

## Phase 1: マイグレーション + デプロイ

### 1-1. マイグレーションSQL作成

```sql
-- sql/migration_add_comment.sql
ALTER TABLE actresses ADD COLUMN comment TEXT DEFAULT NULL AFTER prefectures;
```

### 1-2. 本番DBへ適用

```bash
# SSH接続後
ssh -i ~/.ssh/shinserver_rsa -p 10022 wp2026@sv6810.wpx.ne.jp
php8.3 /home/wp2026/av-hakase.com/public_html/batch/run_migration.php
# または直接MySQL実行
```

### 1-3. コードデプロイ

```bash
# ローカルでコミット
git add meikan/templates/actress.php
git commit -m "女優ページ: AV博士コメント表示追加"

# 本番へデプロイ（deployスキル使用）
```

### 1-4. 確認

- 本番の女優ページを開いてエラーが出ないこと
- コメントなし女優ではコメント欄が表示されないこと

---

## Phase 2: コメント一括生成

### 対象

本番998人全員（commentがNULLの女優）

### 処理方針

| 項目 | 内容 |
|------|------|
| 順序 | 作品数の多い順（人気女優から優先） |
| 並列数 | 5人ずつ並列Agent処理 |
| モデル | sonnet（コスト効率） |
| リサーチ | WebSearch 3〜5クエリ/人 |
| 保存先 | 本番DB（直接書き込み） |

### 2-1. 対象リスト取得（本番DBから）

```bash
ssh 本番 → php8.3でクエリ実行
SELECT a.id, a.name, a.slug, COUNT(aw.work_id) as work_count
FROM actresses a
LEFT JOIN actress_work aw ON a.id = aw.actress_id
WHERE a.comment IS NULL OR a.comment = ''
GROUP BY a.id
ORDER BY work_count DESC
```

### 2-2. バッチ処理フロー（1人あたり）

```
1. 本番DBからプロフィール取得（スリーサイズ・趣味・出身・デビュー）
2. 本番DBからジャンル傾向取得（上位10ジャンル + 件数）
3. WebSearch（並列3クエリ）
   - "{name} AV プレイスタイル 評価"
   - "{name} AV おすすめ作品 シリーズ"
   - "{name} 経歴 趣味 インタビュー"
4. コメント生成（write-actress-commentスキルのルール準拠）
5. 本番DBに保存
   UPDATE actresses SET comment = '...' WHERE id = ?
```

### 2-3. 進捗管理

- 処理済みIDを `/tmp/comment_progress.txt` に都度追記
- エラー発生分は `/tmp/comment_errors.txt` に記録
- 中断・再開が可能な設計

### 2-4. 実行単位

998人を **200人ずつ** 5セッションに分割。
各セッションは5人並列Agentで処理（合計約200並列/セッション相当）。

```
セッション1: rank 1〜200   （作品数最多層）
セッション2: rank 201〜400
セッション3: rank 401〜600
セッション4: rank 601〜800
セッション5: rank 801〜998
```

---

## Phase 3: 確認 + 最終デプロイ

### 3-1. コメント品質チェック（サンプル確認）

- 各セッション後に10件程度を目視確認
- AI文体の定型句混入がないか
- 品番が含まれていないか
- 3〜5文の長さ範囲に収まっているか

### 3-2. 全件保存確認

```sql
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN comment IS NOT NULL AND comment != '' THEN 1 ELSE 0 END) as done,
  SUM(CASE WHEN comment IS NULL OR comment = '' THEN 1 ELSE 0 END) as remaining
FROM actresses
```

### 3-3. キャッシュクリア

```bash
php8.3 /home/wp2026/av-hakase.com/public_html/batch/clear_cache.php
```

---

## コスト試算（目安）

| 項目 | 数量 | 備考 |
|------|------|------|
| WebSearch | 約3,000〜5,000回 | 3〜5クエリ × 998人 |
| AI生成 | 998回 | コメント生成 |
| 作業時間 | 数時間 | 並列処理で圧縮 |

---

## 注意事項

- **本番DBに直接書き込む**ためミスは即影響 → 保存前に確認ステップを挟む
- WebSearchの結果が薄い女優（マイナー・引退済み）は、DBデータのみで生成してフラグを立てる
- 処理中断時は progress.txt から再開できるようにする
- 全件完了後にキャッシュクリアを忘れない

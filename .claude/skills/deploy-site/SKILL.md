---
name: deploy-site
description: "av-hakase.com本番サーバーへのデプロイ。'デプロイ', '本番反映', '本番に上げて', 'deploy', 'push して', 'サーバーに反映' で発動。未コミットの変更がある場合はコミットしてからデプロイする。"
---

# デプロイスキル（av-hakase.com）

ローカルの変更を本番サーバー（sv6810.wpx.ne.jp）に反映するスキル。

---

## サーバー情報

| 項目 | 値 |
|------|-----|
| ホスト | sv6810.wpx.ne.jp |
| ユーザー | wp2026 |
| ポート | 10022 |
| SSH鍵 | ~/.ssh/shinserver_rsa |
| ドキュメントルート | ~/av-hakase.com/public_html/ |
| デプロイ対象 | ローカルの `meikan/` ディレクトリ |

---

## Step 1: 未コミットの変更を確認

```bash
git status
git diff --stat HEAD
```

未コミットの変更がある場合は、内容を確認してコミットメッセージを作成し、コミットする。

**GitHubのSecret Scanning対策**: `.env` 系ファイルや APIキー・トークンを含むファイルが含まれていないか確認する。含まれている場合はコミット対象から除外する。

```bash
git add <変更ファイル>
git commit -m "コミットメッセージ"
```

---

## Step 2: GitHubにpush

```bash
git push origin main
```

**push が Secret Scanning でブロックされた場合:**

1. ブロックされたコミットとファイルを特定する
2. `git-filter-repo` でそのファイルを履歴から除去する

```bash
# git-filter-repo がなければインストール
pip3 install git-filter-repo

# 対象ファイルを履歴から除去（例: gsc/.env）
/Users/kaikyotaro/Library/Python/3.9/bin/git-filter-repo --path <ファイルパス> --invert-paths --force

# remoteが消えるので再追加
git remote add origin https://github.com/kaikyo-1999/video-meikan.git

# force push
git push --force origin main
```

---

## Step 2.5: URL構造の変更チェック（必須）

デプロイ対象の差分にURL構造に影響する変更が含まれていないか確認する。

```bash
git diff HEAD~1 -- meikan/src/Router.php meikan/index.php meikan/config/slug_redirects.php meikan/batch/fix_actress_slugs.php
```

**以下に該当する場合、デプロイ前にユーザーに確認する:**

- 女優・ジャンルのスラグが変更されている（`slug_redirects.php` の差分）
- ルーティングパターンが変更されている（`Router.php` / `index.php` の差分）
- バッチでスラグの一括変更が行われた

**ユーザーへの確認内容:**

1. 旧URLから新URLへの301リダイレクトを設定するか？
2. リダイレクト不要であれば、旧URLが404になることを了承するか？

**リダイレクトが必要な場合**: `config/slug_redirects.php` に旧slug→新slugのマッピングを追加する。`index.php` のリダイレクト処理が自動的にこのファイルを参照して301リダイレクトを行う。

---

## Step 2.6: 記事の@actressタグ 本番DB検証（記事変更時のみ）

記事ファイルに変更がある場合、記事内の `@actress[slug]` タグが **本番DB** に存在するか検証する。
ローカルDBと本番DBでslugが異なるケースがあるため、本番DBに対してチェックすることが重要。

```bash
# 1. 変更された記事から@actressタグを抽出
git diff HEAD~1 --name-only -- meikan/content/articles/ | while read f; do
  grep -oE '@actress\[[a-z0-9-]+\]' "$f" 2>/dev/null
done | sort -u | sed 's/@actress\[//;s/\]//' > /tmp/article_slugs.txt

# 2. 本番DBの女優slugリストを取得
ssh -i ~/.ssh/shinserver_rsa -p 10022 wp2026@sv6810.wpx.ne.jp "php -r \"
define('ROOT_DIR', '/home/wp2026/av-hakase.com/public_html');
require_once ROOT_DIR . '/config/database.php';
\\\$pdo = new PDO('mysql:host=' . DB_HOST . ';dbname=' . DB_NAME . ';charset=utf8mb4', DB_USER, DB_PASS);
\\\$stmt = \\\$pdo->query('SELECT slug FROM actresses');
while(\\\$r = \\\$stmt->fetch(PDO::FETCH_NUM)) echo \\\$r[0] . PHP_EOL;
\"" > /tmp/prod_slugs.txt

# 3. 差分チェック: 記事にあるが本番DBにないslug
comm -23 /tmp/article_slugs.txt /tmp/prod_slugs.txt
```

**本番DBに存在しないslugが検出された場合:**

1. 本番でバッチ実行が必要か確認（新規女優の場合）
2. slug不一致の場合は記事の@actressタグを本番slugに修正
3. 必要に応じて `config/slug_redirects.php` にリダイレクトを追加

---

## Step 3: 本番サーバーにrsyncでデプロイ

```bash
rsync -avz --delete \
  --exclude='.git' \
  --exclude='config/database.php' \
  --exclude='.env' \
  --exclude='.env.local' \
  --exclude='cache/' \
  --exclude='logs/' \
  -e "ssh -i ~/.ssh/shinserver_rsa -p 10022" \
  /Users/kaikyotaro/repository/video-meikan/meikan/ \
  wp2026@sv6810.wpx.ne.jp:~/av-hakase.com/public_html/
```

**除外しているもの（本番環境固有の設定・データ）:**

| 除外パス | 理由 |
|---------|------|
| `config/database.php` | 本番DBの接続情報。上書きしない |
| `.env` / `.env.local` | 本番の環境変数。上書きしない |
| `cache/` | 本番のキャッシュ。削除しない |
| `logs/` | 本番のログ。削除しない |

---

## Step 4: PageSpeed Insights 計測（必須）

デプロイ後、変更が影響するページに対し PageSpeed Insights API を実行し、Lighthouse スコアの劣化がないか確認する。

```bash
# 変更内容に応じて対象URLを決める例
# - テンプレ/CSS/モデル変更: 影響する代表的な女優ページ・ジャンルページ + トップ
# - 記事変更: 該当記事ページ
./scripts/pagespeed.sh "https://av-hakase.com/" mobile
./scripts/pagespeed.sh "https://av-hakase.com/hatano-yui/" mobile
./scripts/pagespeed.sh "https://av-hakase.com/hatano-yui/kyonyu/" mobile
```

サブコマンド:
- `mobile` / `desktop` / `both`
- `--detail` で LCP要素・全Opportunities・Diagnostics・大きいリソースまで展開

**判定基準（Performance スコア）:**

| スコア | 判定 | 対応 |
|---|---|---|
| 90+ | 🟢 OK | そのまま完了 |
| 50-89 | 🟡 要改善 | Top Opportunities をユーザー報告。改善するか確認 |
| 50未満 | 🔴 ブロッキング | 即報告。`./scripts/pagespeed.sh URL mobile --detail` で詳細調査 |

**注意:**
- PageSpeed API は 1リクエスト 30〜60秒かかる。変更ページが多い場合は重要ページに絞る
- 速度劣化は新規追加要素（FANZA等の3rd party script・大きい画像・blocking JS）が主因
- スクリプトは `.env` の `PAGESPEED_API_KEY` を読む（`.gitignore`済み、precam.jp と同じキーを流用可）

**サーバー応答だけ確認したい場合のフォールバック:**

```bash
for url in "https://av-hakase.com/" "https://av-hakase.com/meikan/"; do
  echo "$url → $(curl -o /dev/null -s -w '%{time_total}' "$url")s"
done
```
（PageSpeed APIが使えない時のみ。本来は Step 4 の API 計測を必須とする。）

---

## Step 5: 動作確認（任意）

デプロイ後に本番サイトで変更箇所を確認する。

```bash
# 本番サーバーのPHPファイルを確認する場合
ssh -i ~/.ssh/shinserver_rsa -p 10022 wp2026@sv6810.wpx.ne.jp "ls ~/av-hakase.com/public_html/"
```

---

## 注意事項

- **`cache/` と `logs/` は絶対に `--delete` 対象にしない** — rsyncの `--delete` は除外ディレクトリには適用されないが、除外指定を外すと本番のキャッシュ・ログが全消えする
- **`config/database.php` は上書きしない** — ローカルのDB設定で本番DBに繋いでしまう事故を防ぐ
- **長時間バッチは `nohup` で実行** — SSH切断でプロセスが死ぬため、バッチ実行が必要な場合は `nohup php batch/run_all.php > ~/run_all.log 2>&1 &`
- **デプロイ前に必ずコミット** — 外部ツールやworktreeが変更を上書きするリスクがある

---
name: research-actress
description: "AV女優のプロフィール・経歴・作品情報を効率的にリサーチする。用途に応じて範囲を選択し最短で収集。'女優リサーチ', '女優調査', 'research actress', '候補調査', 'プロフィール確認'で発動。"
metadata:
  version: 1.0.0
---

# 女優リサーチスキル

DB照会を最優先に、必要な情報種別に応じてチェックするドメインを絞り込んで最短でリサーチする。

---

## Step 1: 目的を確認して範囲を決める

ユーザーの目的を確認し、以下の表でリサーチ範囲を選択する：

| 目的 | 収集する情報 | 使うStep |
|-----|------------|---------|
| **記事執筆（基本）** | スリーサイズ・デビュー日・レーベル・代表CID | Step 2→3A |
| **条件別記事（体型系）** | カップ・身長・スリーサイズの確認 | Step 2→3B |
| **条件別記事（経歴系）** | 芸能・アイドル・インフルエンサー歴 | Step 2→3C |
| **候補洗い出し（広め）** | 全情報を浅く収集して絞り込む | Step 2→3A→3B→3C |
| **特定女優の詳細調査** | 全情報を深く収集 | Step 2→3A→3B→3C→3D |

---

## Step 2: DB照会（最速・常に最初に実行）

```bash
cd meikan

# 女優基本情報（slug・デビュー日・作品数）
php -r '
require_once "config/app.php"; require_once "config/database.php"; require_once "src/Database.php"; require_once "src/Cache.php"; require_once "src/models/Actress.php";
$results = Actress::findRecentDebuts(6);
foreach ($results as $r) echo $r["name"] . " | " . $r["slug"] . " | debut: " . $r["debut_date"] . " | works: " . $r["work_count"] . "\n";
'

# 特定女優のslugがわかっている場合 → 作品CID一覧を取得
php -r '
require_once "config/app.php"; require_once "config/database.php"; require_once "src/Database.php"; require_once "src/Cache.php";
$db = Database::getInstance();
$stmt = $db->prepare("SELECT w.source_id, w.title, w.label, w.release_date FROM works w JOIN actress_work aw ON w.id=aw.work_id JOIN actresses a ON aw.actress_id=a.id WHERE a.slug=? ORDER BY w.release_date");
$stmt->execute(["SLUG_HERE"]);
foreach($stmt->fetchAll(PDO::FETCH_ASSOC) as $r) echo $r["source_id"] . " | " . $r["label"] . " | " . $r["release_date"] . " | " . mb_substr($r["title"],0,40) . "\n";
'
```

**DBから取れる情報**: slug・デビュー日・作品数・source_id（CID）・レーベル・作品タイトル
**DBから取れない情報**: 身長・スリーサイズ・カップ・年齢・経歴・SNS

---

## Step 3A: プロフィール情報（身長・スリーサイズ・カップ）

### 参照先（優先順）

| 優先度 | ドメイン | 特徴 | 検索クエリ |
|-------|---------|------|----------|
| 1 | `healingisland3103.com` | ファンブログ。スリーサイズ実測値あり。カップ自動判定可 | `site:healingisland3103.com {女優名}` |
| 2 | `seesaawiki.jp/avsagasou` | wiki形式。多くの女優のプロフィールあり | `site:seesaawiki.jp/avsagasou {女優名}` |
| 3 | FANZAの作品ページ | 公式プロフィール。カップ記載あり | FANZA検索 or 作品URLを直接確認 |
| 4 | メーカー公式サイト | kawaii・S1等は女優プロフページあり | `{メーカー名} {女優名} プロフィール` |

### カップサイズの判定方法（日本規格）

スリーサイズのみ記載されている場合、アンダーバストから推定する：

| バスト−アンダー差 | カップ |
|----------------|------|
| 10〜12.5cm | A |
| 12.5〜15cm | B |
| 15〜17.5cm | C |
| 17.5〜20cm | D |
| 20〜22.5cm | E |
| 22.5〜25cm | F |
| 25〜27.5cm | G |
| 27.5〜30cm | H |
| 30〜32.5cm | I |

healingisland3103.comのB表記（例：B75）はバスト外周。アンダーバストの目安：身長150cm前後は60cm、160cm前後は65cm、170cm前後は70cm。

---

## Step 3B: 年齢・デビュー時年齢

### 参照先（優先順）

| 優先度 | ドメイン | 検索クエリ |
|-------|---------|----------|
| 1 | FANZAの作品タイトル | タイトルに「18歳」「19歳」等が入っている場合そのまま採用 |
| 2 | `healingisland3103.com` | プロフに年齢・生年月日記載あり |
| 3 | Google検索 | `{女優名} 年齢 生年月日` |
| 4 | S1 SDATシリーズ確認 | タイトルに「18〜20歳」特化の場合若年デビューと判定 |

**18歳デビュー判定**: デビュー作品タイトルに「18歳AVデビュー」と明記されているものを採用。不明な場合はS1 SDATシリーズ在籍を根拠に「若年デビュー」と記載。

---

## Step 3C: 経歴・芸能・アイドル・インフルエンサー

### 芸能人・元アイドル調査

| 優先度 | 調べ方 | 検索クエリ |
|-------|-------|----------|
| 1 | Google検索 | `{女優名} 元アイドル`, `{女優名} 芸能` |
| 2 | デビュー作タイトル確認 | タイトルに「元○○」「元アイドル」「子役」等が含まれているか |
| 3 | アイドルDB・まとめサイト | `{グループ名または旧芸名} {女優名}` |
| 4 | Wikipedia | `{女優名}` |

**元アイドル判定基準**: アイドルグループ在籍歴（地下アイドル含む）。グラビアアイドルは「芸能人」扱い（元アイドルとは区別）。

### インフルエンサー調査

| 優先度 | 調べ方 | 検索クエリ |
|-------|-------|----------|
| 1 | Twitter/X直接検索 | `{女優名}` でアカウント検索・フォロワー数確認 |
| 2 | Instagram検索 | 同上 |
| 3 | TikTok検索 | `{女優名}` |
| 4 | Google検索 | `{女優名} フォロワー`, `{女優名} SNS` |

**インフルエンサー判定基準**: いずれかのSNSでフォロワー1万人以上。または作品タイトルに「SNS人気」「TikToker」等の記載あり。

---

## Step 3D: 作品情報・CID取得

### CIDの確認方法（優先順）

1. **DBにある場合**: Step 2の `source_id` がCID
2. **DBにない場合**: FANZAで女優名検索 → 作品URLの `cid=XXXX` を確認
3. **画像URLのCID確認**: FANZAリンクのCIDが `1sone00221` 形式の場合、画像URLでは `sone00221`（1プレフィックスを除く）

### 画像URLの存在確認（必須）

```bash
CID="XXXXXX"
# 最大jp番号を探す
for n in 10 9 8 7 6 5 4 3; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://pics.dmm.co.jp/digital/video/${CID}/${CID}jp-${n}.jpg")
  [ "$code" = "200" ] && echo "最大: jp-${n}" && break
done
```

---

## Step 4: 結果をまとめて報告

収集した情報を以下のフォーマットで整理して報告する：

```
## {女優名} リサーチ結果

### 基本プロフィール
- slug: {slug}
- デビュー日: {YYYY-MM-DD}
- 身長: {cm} / スリーサイズ: {B/W/H（カップ）}
- 年齢（デビュー時）: {歳}
- レーベル: {レーベル名}

### 作品情報
- 代表CID: {CID}（画像最大: jp-{N}）
- 作品数: {N}本
- デビュー作タイトル: {タイトル}

### 経歴・特徴
- 条件該当: {爆乳/小柄/元アイドル/芸能人/インフルエンサー等}
- 経歴: {概要}
- SNS: {フォロワー数・URL または なし}

### 情報ソース
- {healingisland3103.com / seesaawiki / FANZA / Google等}
```

---

## 補足: 候補洗い出しモード

記事のために複数女優を一括調査する場合：

1. DB照会で候補全員をリストアップ
2. **条件に合致するか** を作品タイトル・ジャンルで一次スクリーニング（Web検索不要）
3. 残った候補のみ Step 3A〜3C で詳細調査
4. 結果をテーブル形式で一覧提示してユーザーに確認

```
| 女優名 | 条件 | 根拠 | 信頼度 |
|-------|------|------|-------|
| 清野咲 | Cカップ | healingisland: B75/W52/H88 → C確定 | 高 |
| 當真さら | 推定C | 公開情報なし・視聴者評価 | 低 |
```

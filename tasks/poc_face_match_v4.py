#!/usr/bin/env python3
"""
PoC v4: 名前フィルタ + 多数決 + 一貫性チェック
v3の66件結果に対して3つの改善を適用し、偽陽性を弾けるか検証する
"""

import face_recognition
import urllib.request
import tempfile
import os
import json
import re
import numpy as np

REF_PROFILE = "http://pics.dmm.co.jp/mono/actjpgs/nizimura_yumi.jpg"
REF_WORK_SAMPLES = [
    "https://pics.dmm.co.jp/digital/video/miab00583/miab00583jp-1.jpg",
    "https://pics.dmm.co.jp/digital/video/miab00583/miab00583jp-2.jpg",
    "https://pics.dmm.co.jp/digital/video/miab00583/miab00583jp-3.jpg",
    "https://pics.dmm.co.jp/digital/video/midv00863/midv00863jp-1.jpg",
    "https://pics.dmm.co.jp/digital/video/midv00863/midv00863jp-2.jpg",
    "https://pics.dmm.co.jp/digital/video/midv00863/midv00863jp-3.jpg",
    "https://pics.dmm.co.jp/digital/video/24bld00008/24bld00008jp-1.jpg",
    "https://pics.dmm.co.jp/digital/video/24bld00008/24bld00008jp-2.jpg",
    "https://pics.dmm.co.jp/digital/video/24bld00008/24bld00008jp-3.jpg",
]

# 目視確認済みの正解データ
# v2で合格した12件
TRUE_POSITIVES = {
    "smgn042", "orecz477", "nost205", "spay726", "spay722",
    "kure023", "pai228", "orecz437", "spay710", "deas040",
    "debz001", "nost173",
}
# v2で不合格 + 今回不合格
FALSE_POSITIVES = {
    # v2
    "ddh377", "simp014", "msodn997", "lady549", "tkk082",
    # 今回 #50-54
    "eqt072", "urf0045", "scute304", "dht154", "mywife193",
    # #44-48
    "big0052", "endx507", "instc253", "instc245", "happyf049",
    # #42
    "infc010",
    # #38
    "mfcs039",
    # #31-33
    "garea257", "eko030", "dage598",
}


def download_image(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            with open(path, "wb") as f:
                f.write(resp.read())
        return True
    except:
        return False

def get_face_encodings(image_path):
    try:
        img = face_recognition.load_image_file(image_path)
        return face_recognition.face_encodings(img)
    except:
        return []


def name_matches_yumi(title):
    """
    「ゆみ」が名前の先頭にあるかチェック。
    OK: ゆみ, ゆみちゃん, ユミ, Yumi, YUMI, yumiちゃん, ゆみ＆ふう, にじむ, 虹村
    NG: あゆみ, まゆみ, 亜由美, 高森あゆみ, ayumi, muyumi, 友美, 本間祐美香
    """
    t = title.strip()

    # 虹村/にじむ を含む → OK
    if '虹村' in t or 'にじむ' in t:
        return True

    # タイトルが ゆみ/ユミ で始まる（＆区切りの各パートもチェック）
    parts = re.split(r'[＆&]', t)
    for part in parts:
        part = part.strip()
        if re.match(r'^(ゆみ|ユミ)', part):
            return True
        if re.match(r'^[Yy][Uu][Mm][Ii]($|[^a-zA-Z])', part):
            return True

    return False


def main():
    tmpdir = tempfile.mkdtemp()

    # === 基準画像 ===
    print("=== 基準画像の読み込み ===", flush=True)
    ref_encodings = []

    ref_path = os.path.join(tmpdir, "ref_profile.jpg")
    if download_image(REF_PROFILE, ref_path):
        encs = get_face_encodings(ref_path)
        ref_encodings.extend(encs)
        print(f"  プロフィール画像: {len(encs)}顔", flush=True)

    for i, url in enumerate(REF_WORK_SAMPLES):
        img_path = os.path.join(tmpdir, f"ref_{i}.jpg")
        if download_image(url, img_path):
            encs = get_face_encodings(img_path)
            ref_encodings.extend(encs)

    print(f"  合計基準顔: {len(ref_encodings)}個\n", flush=True)
    ref_encodings_np = np.array(ref_encodings)
    num_refs = len(ref_encodings)

    # === v3の66件結果を読み込み ===
    results_path = os.path.join(os.path.dirname(__file__), 'face_match_results.json')
    with open(results_path) as f:
        v3_data = json.load(f)

    # 全705件分のデータも必要（名前フィルタテスト用）
    # ここではv3のmatch結果 + 既知のFPを検証対象にする

    # === テスト1: 名前フィルタ単体の効果 ===
    print("=" * 70)
    print("テスト1: 名前フィルタ単体")
    print("=" * 70)

    all_cids = list(TRUE_POSITIVES | FALSE_POSITIVES)
    # v3結果からタイトル取得
    title_map = {m['cid']: m['title'] for m in v3_data['matches']}
    # FPでv3にマッチしなかったもののタイトルも追加
    extra_titles = {
        "ddh377": "ゆみ", "simp014": "ユミ", "msodn997": "あゆみ",
        "lady549": "あゆみ", "tkk082": "本上まゆみ",
    }
    title_map.update(extra_titles)

    name_tp = 0  # True positive kept
    name_fp = 0  # False positive kept (bad)
    name_fn = 0  # True positive rejected (bad)
    name_tn = 0  # False positive rejected (good)

    print(f"\n{'CID':<15} {'Title':<20} {'Name OK':>8} {'実際':>6} {'判定':>6}")
    print("-" * 60)

    for cid in sorted(all_cids):
        title = title_map.get(cid, "?")
        is_tp = cid in TRUE_POSITIVES
        passes = name_matches_yumi(title)

        if is_tp and passes: name_tp += 1; judge = "✓"
        elif is_tp and not passes: name_fn += 1; judge = "✗見逃し"
        elif not is_tp and passes: name_fp += 1; judge = "✗通過"
        else: name_tn += 1; judge = "✓弾いた"

        actual = "本人" if is_tp else "別人"
        print(f"{cid:<15} {title:<20} {'○' if passes else '×':>8} {actual:>6} {judge:>6}")

    print(f"\n名前フィルタ: TP={name_tp} TN={name_tn} FP={name_fp} FN={name_fn}")
    print(f"  弾けた偽陽性: {name_tn}/{len(FALSE_POSITIVES)}")

    # === テスト2: 多数決 + 一貫性チェック（v3の66件で顔再照合） ===
    print(f"\n{'=' * 70}")
    print("テスト2: 多数決 + 一貫性チェック（v3マッチ66件を再照合）")
    print("=" * 70)

    # v3でマッチした66件のうち、TP/FPが確定しているものを再照合
    known_matches = [m for m in v3_data['matches'] if m['cid'] in (TRUE_POSITIVES | FALSE_POSITIVES)]

    print(f"\n{'CID':<15} {'Title':<15} {'AvgDist':>8} {'Vote':>6} {'Consist':>8} {'実際':>6} {'A':>3} {'C':>3} {'A+C':>4}")
    print("-" * 80)

    for m in known_matches:
        cid = m['cid']
        title = m['title']
        is_tp = cid in TRUE_POSITIVES

        # サムネイル + サンプル画像をDL
        thumb_url = f"https://pics.dmm.co.jp/digital/amateur/{cid}/{cid}jm.jpg"
        sample_urls = [f"https://pics.dmm.co.jp/digital/amateur/{cid}/{cid}jp-{i:03d}.jpg" for i in range(1, 4)]
        all_urls = [thumb_url] + sample_urls

        # 画像ごとに顔を検出し、どの画像からマッチしたかを記録
        per_image_results = []  # (image_idx, best_avg_dist, num_refs_matched)

        for img_idx, url in enumerate(all_urls):
            img_path = os.path.join(tmpdir, f"v4_{cid}_{img_idx}.jpg")
            if not download_image(url, img_path):
                continue
            encs = get_face_encodings(img_path)
            if os.path.exists(img_path):
                os.remove(img_path)
            if not encs:
                continue

            # この画像の各顔について、基準顔群との距離を計算
            for enc in encs:
                distances = face_recognition.face_distance(ref_encodings_np, enc)
                avg_dist = np.mean(distances)

                # 多数決: 基準顔のうち何個が0.48未満か
                votes = sum(1 for d in distances if d < 0.48)

                per_image_results.append({
                    'img_idx': img_idx,
                    'avg_dist': avg_dist,
                    'votes': votes,
                    'distances': distances,
                })

        if not per_image_results:
            continue

        # 最も良い顔のスコアを取得
        best = min(per_image_results, key=lambda x: x['avg_dist'])
        avg_dist = best['avg_dist']
        best_votes = best['votes']

        # A: 多数決 — 基準顔の過半数(2/3以上)で0.48未満
        majority = num_refs // 2 + 1
        pass_a = best_votes >= majority

        # C: 一貫性 — 複数画像からマッチする顔があるか（2枚以上の画像でavg<0.48）
        matching_images = set()
        for r in per_image_results:
            if r['avg_dist'] < 0.48:
                matching_images.add(r['img_idx'])
        pass_c = len(matching_images) >= 2

        pass_ac = pass_a and pass_c

        actual = "本人" if is_tp else "別人"
        a_mark = "✓" if (pass_a == is_tp) or (not pass_a and not is_tp) else "✗"
        c_mark = "✓" if (pass_c == is_tp) or (not pass_c and not is_tp) else "✗"
        ac_mark = "✓" if (pass_ac == is_tp) or (not pass_ac and not is_tp) else "✗"

        print(f"{cid:<15} {title[:15]:<15} {avg_dist:>8.4f} {best_votes:>4}/{num_refs} {'Y' if pass_c else 'N':>8} {actual:>6} {a_mark:>3} {c_mark:>3} {ac_mark:>4}")

    # === テスト3: 名前フィルタ + A + C 全組み合わせ ===
    print(f"\n{'=' * 70}")
    print("テスト3: 全フィルタ組み合わせの精度サマリー")
    print("=" * 70)

    results_summary = []
    for m in known_matches:
        cid = m['cid']
        title = m['title']
        is_tp = cid in TRUE_POSITIVES

        passes_name = name_matches_yumi(title)

        # 顔照合結果を再利用するため、もう一度計算
        thumb_url = f"https://pics.dmm.co.jp/digital/amateur/{cid}/{cid}jm.jpg"
        sample_urls = [f"https://pics.dmm.co.jp/digital/amateur/{cid}/{cid}jp-{i:03d}.jpg" for i in range(1, 4)]
        all_urls = [thumb_url] + sample_urls

        per_image_results = []
        for img_idx, url in enumerate(all_urls):
            img_path = os.path.join(tmpdir, f"v4b_{cid}_{img_idx}.jpg")
            if not download_image(url, img_path):
                continue
            encs = get_face_encodings(img_path)
            if os.path.exists(img_path):
                os.remove(img_path)
            if not encs:
                continue
            for enc in encs:
                distances = face_recognition.face_distance(ref_encodings_np, enc)
                per_image_results.append({
                    'img_idx': img_idx,
                    'avg_dist': np.mean(distances),
                    'votes': sum(1 for d in distances if d < 0.48),
                })

        if not per_image_results:
            results_summary.append((cid, title, is_tp, passes_name, False, False))
            continue

        best = min(per_image_results, key=lambda x: x['avg_dist'])
        majority = num_refs // 2 + 1
        pass_a = best['votes'] >= majority

        matching_images = set()
        for r in per_image_results:
            if r['avg_dist'] < 0.48:
                matching_images.add(r['img_idx'])
        pass_c = len(matching_images) >= 2

        results_summary.append((cid, title, is_tp, passes_name, pass_a, pass_c))

    combos = {
        "v3のみ(avg<0.46)":       lambda n, a, c: True,
        "名前フィルタのみ":         lambda n, a, c: n,
        "多数決(A)のみ":           lambda n, a, c: a,
        "一貫性(C)のみ":           lambda n, a, c: c,
        "名前 + A":              lambda n, a, c: n and a,
        "名前 + C":              lambda n, a, c: n and c,
        "A + C":                lambda n, a, c: a and c,
        "名前 + A + C":          lambda n, a, c: n and a and c,
    }

    print(f"\n{'方式':<25} {'TP':>4} {'TN':>4} {'FP':>4} {'FN':>4} {'精度':>8} {'適合率':>8} {'再現率':>8}")
    print("-" * 80)

    for label, fn in combos.items():
        tp = fp = tn = fn_count = 0
        for cid, title, is_tp, passes_name, pass_a, pass_c in results_summary:
            passes = fn(passes_name, pass_a, pass_c)
            if is_tp and passes: tp += 1
            elif is_tp and not passes: fn_count += 1
            elif not is_tp and passes: fp += 1
            else: tn += 1

        total = tp + tn + fp + fn_count
        accuracy = (tp + tn) / total if total else 0
        precision = tp / (tp + fp) if (tp + fp) else 0
        recall = tp / (tp + fn_count) if (tp + fn_count) else 0

        print(f"{label:<25} {tp:>4} {tn:>4} {fp:>4} {fn_count:>4} {accuracy:>7.1%} {precision:>7.1%} {recall:>7.1%}")


if __name__ == "__main__":
    main()

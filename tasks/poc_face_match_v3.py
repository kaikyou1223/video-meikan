#!/usr/bin/env python3
"""
PoC v3: 基準画像を複数枚に増やして精度改善
- 基準: プロフィール画像 + 単体作品のサンプル画像から顔検出（複数エンコーディング）
- 照合: サムネイル + サンプル3枚の全画像から顔検出
- 判定: 基準顔群との平均距離で判定（外れ値に強い）
"""

import face_recognition
import urllib.request
import tempfile
import os
import numpy as np

REF_PROFILE = "http://pics.dmm.co.jp/mono/actjpgs/nizimura_yumi.jpg"

# 単体作品のサンプル画像（虹村ゆみ確定の作品から各3枚）
REF_WORK_SAMPLES = [
    # miab00583 - 単体作品
    "https://pics.dmm.co.jp/digital/video/miab00583/miab00583jp-1.jpg",
    "https://pics.dmm.co.jp/digital/video/miab00583/miab00583jp-2.jpg",
    "https://pics.dmm.co.jp/digital/video/miab00583/miab00583jp-3.jpg",
    # midv00863 - 単体作品
    "https://pics.dmm.co.jp/digital/video/midv00863/midv00863jp-1.jpg",
    "https://pics.dmm.co.jp/digital/video/midv00863/midv00863jp-2.jpg",
    "https://pics.dmm.co.jp/digital/video/midv00863/midv00863jp-3.jpg",
    # 24bld00008 - 単体作品
    "https://pics.dmm.co.jp/digital/video/24bld00008/24bld00008jp-1.jpg",
    "https://pics.dmm.co.jp/digital/video/24bld00008/24bld00008jp-2.jpg",
    "https://pics.dmm.co.jp/digital/video/24bld00008/24bld00008jp-3.jpg",
]

# 素人作品ターゲット（前回と同じ20件）
RAW = """smgn042|ゆみ＆ふう|https://pics.dmm.co.jp/digital/amateur/smgn042/smgn042jm.jpg|https://pics.dmm.co.jp/digital/amateur/smgn042/smgn042jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/smgn042/smgn042jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/smgn042/smgn042jp-003.jpg
tkk082|本上まゆみ|https://pics.dmm.co.jp/digital/amateur/tkk082/tkk082jm.jpg|https://pics.dmm.co.jp/digital/amateur/tkk082/tkk082jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/tkk082/tkk082jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/tkk082/tkk082jp-003.jpg
lady549|あゆみ|https://pics.dmm.co.jp/digital/amateur/lady549/lady549jm.jpg|https://pics.dmm.co.jp/digital/amateur/lady549/lady549jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/lady549/lady549jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/lady549/lady549jp-003.jpg
orecz477|ゆみちゃん|https://pics.dmm.co.jp/digital/amateur/orecz477/orecz477jm.jpg|https://pics.dmm.co.jp/digital/amateur/orecz477/orecz477jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/orecz477/orecz477jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/orecz477/orecz477jp-003.jpg
nost205|ゆみさん|https://pics.dmm.co.jp/digital/amateur/nost205/nost205jm.jpg|https://pics.dmm.co.jp/digital/amateur/nost205/nost205jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/nost205/nost205jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/nost205/nost205jp-003.jpg
spay726|ゆみ|https://pics.dmm.co.jp/digital/amateur/spay726/spay726jm.jpg|https://pics.dmm.co.jp/digital/amateur/spay726/spay726jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/spay726/spay726jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/spay726/spay726jp-003.jpg
spay722|ゆみ|https://pics.dmm.co.jp/digital/amateur/spay722/spay722jm.jpg|https://pics.dmm.co.jp/digital/amateur/spay722/spay722jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/spay722/spay722jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/spay722/spay722jp-003.jpg
pwife1207|ゆみ|https://pics.dmm.co.jp/digital/amateur/pwife1207/pwife1207jm.jpg|https://pics.dmm.co.jp/digital/amateur/pwife1207/pwife1207jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/pwife1207/pwife1207jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/pwife1207/pwife1207jp-003.jpg
kure023|ゆみ＆まこ|https://pics.dmm.co.jp/digital/amateur/kure023/kure023jm.jpg|https://pics.dmm.co.jp/digital/amateur/kure023/kure023jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/kure023/kure023jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/kure023/kure023jp-003.jpg
msodn997|あゆみ|https://pics.dmm.co.jp/digital/amateur/msodn997/msodn997jm.jpg|https://pics.dmm.co.jp/digital/amateur/msodn997/msodn997jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/msodn997/msodn997jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/msodn997/msodn997jp-003.jpg
pai228|にじむ|https://pics.dmm.co.jp/digital/amateur/pai228/pai228jm.jpg|https://pics.dmm.co.jp/digital/amateur/pai228/pai228jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/pai228/pai228jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/pai228/pai228jp-003.jpg
orecz437|ゆみ|https://pics.dmm.co.jp/digital/amateur/orecz437/orecz437jm.jpg|https://pics.dmm.co.jp/digital/amateur/orecz437/orecz437jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/orecz437/orecz437jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/orecz437/orecz437jp-003.jpg
simp014|ユミ|https://pics.dmm.co.jp/digital/amateur/simp014/simp014jm.jpg|https://pics.dmm.co.jp/digital/amateur/simp014/simp014jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/simp014/simp014jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/simp014/simp014jp-003.jpg
spay710|ゆみ|https://pics.dmm.co.jp/digital/amateur/spay710/spay710jm.jpg|https://pics.dmm.co.jp/digital/amateur/spay710/spay710jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/spay710/spay710jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/spay710/spay710jp-003.jpg
deas040|ゆみ＆おと＆まこ|https://pics.dmm.co.jp/digital/amateur/deas040/deas040jm.jpg|https://pics.dmm.co.jp/digital/amateur/deas040/deas040jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/deas040/deas040jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/deas040/deas040jp-003.jpg
mfcs195|ゆみにー|https://pics.dmm.co.jp/digital/amateur/mfcs195/mfcs195jm.jpg|https://pics.dmm.co.jp/digital/amateur/mfcs195/mfcs195jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/mfcs195/mfcs195jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/mfcs195/mfcs195jp-003.jpg
hdsn090|ゆみ|https://pics.dmm.co.jp/digital/amateur/hdsn090/hdsn090jm.jpg|https://pics.dmm.co.jp/digital/amateur/hdsn090/hdsn090jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/hdsn090/hdsn090jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/hdsn090/hdsn090jp-003.jpg
ddh377|ゆみ|https://pics.dmm.co.jp/digital/amateur/ddh377/ddh377jm.jpg|https://pics.dmm.co.jp/digital/amateur/ddh377/ddh377jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/ddh377/ddh377jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/ddh377/ddh377jp-003.jpg
debz001|ゆみちゃん|https://pics.dmm.co.jp/digital/amateur/debz001/debz001jm.jpg|https://pics.dmm.co.jp/digital/amateur/debz001/debz001jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/debz001/debz001jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/debz001/debz001jp-003.jpg
nost173|ゆみ|https://pics.dmm.co.jp/digital/amateur/nost173/nost173jm.jpg|https://pics.dmm.co.jp/digital/amateur/nost173/nost173jp-001.jpg,https://pics.dmm.co.jp/digital/amateur/nost173/nost173jp-002.jpg,https://pics.dmm.co.jp/digital/amateur/nost173/nost173jp-003.jpg"""

# 目視で確認済みの別人リスト（精度検証用）
FALSE_POSITIVES = {"ddh377", "simp014", "msodn997", "lady549", "tkk082"}

def parse_targets():
    targets = []
    for line in RAW.strip().split("\n"):
        parts = line.split("|")
        cid, title, thumb = parts[0], parts[1], parts[2]
        samples = parts[3].split(",") if len(parts) > 3 and parts[3] else []
        targets.append((cid, title, thumb, samples))
    return targets

def download_image(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            with open(path, "wb") as f:
                f.write(resp.read())
        return True
    except:
        return False

def get_face_encodings(image_path):
    img = face_recognition.load_image_file(image_path)
    return face_recognition.face_encodings(img)

def calc_avg_min_distance(ref_encodings, target_encodings):
    """
    各ターゲット顔について、全基準顔との距離の平均を計算。
    その中で最小のもの（最も本人に近い顔）を返す。
    """
    best_avg = float('inf')
    for t_enc in target_encodings:
        distances = face_recognition.face_distance(ref_encodings, t_enc)
        avg_dist = np.mean(distances)
        if avg_dist < best_avg:
            best_avg = avg_dist
    return best_avg

def main():
    tmpdir = tempfile.mkdtemp()
    targets = parse_targets()

    # === 基準画像の読み込み ===
    print("=== 基準画像の読み込み ===")
    ref_encodings = []

    # プロフィール画像
    ref_path = os.path.join(tmpdir, "ref_profile.jpg")
    if download_image(REF_PROFILE, ref_path):
        encs = get_face_encodings(ref_path)
        ref_encodings.extend(encs)
        print(f"  プロフィール画像: {len(encs)}顔検出")

    # 単体作品のサンプル画像
    for i, url in enumerate(REF_WORK_SAMPLES):
        img_path = os.path.join(tmpdir, f"ref_sample_{i}.jpg")
        if download_image(url, img_path):
            encs = get_face_encodings(img_path)
            ref_encodings.extend(encs)

    print(f"  作品サンプル {len(REF_WORK_SAMPLES)}枚から顔検出")
    print(f"  合計基準顔: {len(ref_encodings)}個\n")

    if len(ref_encodings) < 2:
        print("基準顔が不足しています")
        return

    ref_encodings = np.array(ref_encodings)

    # === ターゲット照合 ===
    print(f"{'CID':<15} {'Title':<15} {'Faces':>5} {'AvgDist':>10} {'Match':>6} {'Correct':>8}")
    print("-" * 70)

    for cid, title, thumb, samples in targets:
        all_urls = [thumb] + samples
        all_encodings = []

        for i, url in enumerate(all_urls):
            img_path = os.path.join(tmpdir, f"{cid}_{i}.jpg")
            if download_image(url, img_path):
                encs = get_face_encodings(img_path)
                all_encodings.extend(encs)

        if not all_encodings:
            print(f"{cid:<15} {title:<15} {'0':>5} {'N/A':>10} {'--':>6}")
            continue

        avg_dist = calc_avg_min_distance(ref_encodings, all_encodings)
        is_match = avg_dist < 0.45  # 閾値は後で調整
        is_known_fp = cid in FALSE_POSITIVES

        status = "★HIT" if is_match else ""
        # 正解判定: マッチ&非FP=✓, 非マッチ&FP=✓, それ以外=✗
        if is_known_fp:
            correct = "✓" if not is_match else "✗FP"
        else:
            correct = "✓" if is_match else "?miss"

        print(f"{cid:<15} {title:<15} {len(all_encodings):>5} {avg_dist:>10.4f} {status:>6} {correct:>8}")

    # === v2との比較用に閾値ごとの精度も出す ===
    print("\n=== 閾値別の精度シミュレーション ===")
    print("(FP=偽陽性=別人をマッチ判定, FN=偽陰性=本人を見逃し)")

    results = []
    for cid, title, thumb, samples in targets:
        all_urls = [thumb] + samples
        all_encodings = []
        for i, url in enumerate(all_urls):
            img_path = os.path.join(tmpdir, f"{cid}_{i}.jpg")
            if os.path.exists(img_path):
                encs = get_face_encodings(img_path)
                all_encodings.extend(encs)

        if not all_encodings:
            results.append((cid, None, cid in FALSE_POSITIVES))
            continue

        avg_dist = calc_avg_min_distance(ref_encodings, all_encodings)
        results.append((cid, avg_dist, cid in FALSE_POSITIVES))

    for threshold in [0.38, 0.40, 0.42, 0.44, 0.46]:
        fp = sum(1 for cid, d, is_fp in results if d is not None and d < threshold and is_fp)
        fn = sum(1 for cid, d, is_fp in results if d is not None and d >= threshold and not is_fp)
        tp = sum(1 for cid, d, is_fp in results if d is not None and d < threshold and not is_fp)
        tn = sum(1 for cid, d, is_fp in results if d is not None and d >= threshold and is_fp)
        no_face = sum(1 for cid, d, _ in results if d is None)
        print(f"  閾値{threshold:.2f}: TP={tp} TN={tn} FP={fp} FN={fn} (顔なし={no_face})")

if __name__ == "__main__":
    main()

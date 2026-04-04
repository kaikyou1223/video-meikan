#!/usr/bin/env python3
"""
PoC: 素人作品の顔マッチング
虹村ゆみの基準画像と、videoc「ゆみ」検索結果のサムネイルを顔認識で照合する
"""

import face_recognition
import urllib.request
import tempfile
import os

REF_URL = "http://pics.dmm.co.jp/mono/actjpgs/nizimura_yumi.jpg"

TARGETS = [
    ("smgn042", "ゆみ＆ふう", "https://pics.dmm.co.jp/digital/amateur/smgn042/smgn042jm.jpg"),
    ("tkk082", "本上まゆみ", "https://pics.dmm.co.jp/digital/amateur/tkk082/tkk082jm.jpg"),
    ("lady549", "あゆみ", "https://pics.dmm.co.jp/digital/amateur/lady549/lady549jm.jpg"),
    ("orecz477", "ゆみちゃん", "https://pics.dmm.co.jp/digital/amateur/orecz477/orecz477jm.jpg"),
    ("nost205", "ゆみさん", "https://pics.dmm.co.jp/digital/amateur/nost205/nost205jm.jpg"),
    ("spay726", "ゆみ", "https://pics.dmm.co.jp/digital/amateur/spay726/spay726jm.jpg"),
    ("spay722", "ゆみ", "https://pics.dmm.co.jp/digital/amateur/spay722/spay722jm.jpg"),
    ("pwife1207", "ゆみ", "https://pics.dmm.co.jp/digital/amateur/pwife1207/pwife1207jm.jpg"),
    ("kure023", "ゆみ＆まこ", "https://pics.dmm.co.jp/digital/amateur/kure023/kure023jm.jpg"),
    ("msodn997", "あゆみ", "https://pics.dmm.co.jp/digital/amateur/msodn997/msodn997jm.jpg"),
    ("pai228", "にじむ", "https://pics.dmm.co.jp/digital/amateur/pai228/pai228jm.jpg"),
    ("orecz437", "ゆみ", "https://pics.dmm.co.jp/digital/amateur/orecz437/orecz437jm.jpg"),
    ("simp014", "ユミ", "https://pics.dmm.co.jp/digital/amateur/simp014/simp014jm.jpg"),
    ("spay710", "ゆみ", "https://pics.dmm.co.jp/digital/amateur/spay710/spay710jm.jpg"),
    ("deas040", "ゆみ＆おと＆まこ", "https://pics.dmm.co.jp/digital/amateur/deas040/deas040jm.jpg"),
    ("mfcs195", "ゆみにー", "https://pics.dmm.co.jp/digital/amateur/mfcs195/mfcs195jm.jpg"),
    ("hdsn090", "ゆみ", "https://pics.dmm.co.jp/digital/amateur/hdsn090/hdsn090jm.jpg"),
    ("ddh377", "ゆみ", "https://pics.dmm.co.jp/digital/amateur/ddh377/ddh377jm.jpg"),
    ("debz001", "ゆみちゃん", "https://pics.dmm.co.jp/digital/amateur/debz001/debz001jm.jpg"),
    ("nost173", "ゆみ", "https://pics.dmm.co.jp/digital/amateur/nost173/nost173jm.jpg"),
]

def download_image(url, path):
    """画像をダウンロード"""
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            with open(path, "wb") as f:
                f.write(resp.read())
        return True
    except Exception as e:
        print(f"  DL失敗: {e}")
        return False

def get_face_encoding(image_path):
    """画像から顔エンコーディングを取得"""
    img = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(img)
    return encodings

def main():
    tmpdir = tempfile.mkdtemp()

    # 基準画像をダウンロード
    ref_path = os.path.join(tmpdir, "reference.jpg")
    print(f"基準画像DL: {REF_URL}")
    if not download_image(REF_URL, ref_path):
        print("基準画像のDLに失敗")
        return

    ref_encodings = get_face_encoding(ref_path)
    if not ref_encodings:
        print("基準画像から顔を検出できませんでした")
        return
    ref_encoding = ref_encodings[0]
    print(f"基準画像: 顔{len(ref_encodings)}個検出\n")

    # 各ターゲットと照合
    print(f"{'CID':<15} {'Title':<20} {'Faces':>5} {'Distance':>10} {'Match':>6}")
    print("-" * 65)

    matches = []
    for cid, title, url in TARGETS:
        target_path = os.path.join(tmpdir, f"{cid}.jpg")
        if not download_image(url, target_path):
            print(f"{cid:<15} {title:<20} {'DL失敗':>5}")
            continue

        target_encodings = get_face_encoding(target_path)
        if not target_encodings:
            print(f"{cid:<15} {title:<20} {'0':>5} {'N/A':>10} {'--':>6}")
            continue

        # 全検出顔のうち最も近いものを採用
        distances = face_recognition.face_distance(target_encodings, ref_encoding)
        min_dist = min(distances)
        is_match = min_dist < 0.5  # 閾値0.5（厳しめ）

        status = "★HIT" if is_match else ""
        print(f"{cid:<15} {title:<20} {len(target_encodings):>5} {min_dist:>10.4f} {status:>6}")

        if is_match:
            matches.append((cid, title, min_dist))

    print(f"\n=== 結果: {len(matches)}/{len(TARGETS)}件マッチ ===")
    for cid, title, dist in matches:
        print(f"  ★ {cid} ({title}) - distance: {dist:.4f}")
        print(f"    https://www.dmm.co.jp/digital/amateur/-/detail/=/cid={cid}/")

if __name__ == "__main__":
    main()

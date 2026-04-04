#!/usr/bin/env python3
"""
PoC v2: サンプル画像も使った顔マッチング
サムネイル + サンプル画像3枚から顔検出し、基準画像と照合
"""

import face_recognition
import urllib.request
import tempfile
import os

REF_URL = "http://pics.dmm.co.jp/mono/actjpgs/nizimura_yumi.jpg"

# (cid, title, thumbnail, [sample1, sample2, sample3])
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
    except Exception:
        return False

def get_face_encodings(image_path):
    img = face_recognition.load_image_file(image_path)
    return face_recognition.face_encodings(img)

def main():
    tmpdir = tempfile.mkdtemp()
    targets = parse_targets()

    # 基準画像
    ref_path = os.path.join(tmpdir, "reference.jpg")
    print(f"基準画像DL: {REF_URL}")
    if not download_image(REF_URL, ref_path):
        print("基準画像のDLに失敗")
        return

    ref_encodings = get_face_encodings(ref_path)
    if not ref_encodings:
        print("基準画像から顔を検出できませんでした")
        return
    ref_encoding = ref_encodings[0]
    print(f"基準画像: 顔{len(ref_encodings)}個検出\n")

    print(f"{'CID':<15} {'Title':<15} {'Imgs':>4} {'Faces':>5} {'BestDist':>10} {'Match':>6}")
    print("-" * 65)

    matches = []
    for cid, title, thumb, samples in targets:
        # サムネイル + サンプル画像を全部DL&顔検出
        all_urls = [thumb] + samples
        all_encodings = []
        dl_count = 0

        for i, url in enumerate(all_urls):
            img_path = os.path.join(tmpdir, f"{cid}_{i}.jpg")
            if download_image(url, img_path):
                dl_count += 1
                encs = get_face_encodings(img_path)
                all_encodings.extend(encs)

        if not all_encodings:
            display_title = title[:15] if len(title.encode('utf-8')) <= 30 else title[:8]
            print(f"{cid:<15} {title:<15} {dl_count:>4} {'0':>5} {'N/A':>10} {'--':>6}")
            continue

        # 全検出顔のうち最も近いものを採用
        distances = face_recognition.face_distance(all_encodings, ref_encoding)
        min_dist = min(distances)
        is_match = min_dist < 0.5

        status = "★HIT" if is_match else ""
        print(f"{cid:<15} {title:<15} {dl_count:>4} {len(all_encodings):>5} {min_dist:>10.4f} {status:>6}")

        if is_match:
            matches.append((cid, title, min_dist))

    print(f"\n=== 結果: {len(matches)}/{len(targets)}件マッチ (閾値 < 0.5) ===")
    for cid, title, dist in sorted(matches, key=lambda x: x[2]):
        print(f"  ★ {cid} ({title}) - distance: {dist:.4f}")
        print(f"    https://www.dmm.co.jp/digital/amateur/-/detail/=/cid={cid}/")

if __name__ == "__main__":
    main()

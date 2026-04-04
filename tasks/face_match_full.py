#!/usr/bin/env python3
"""
虹村ゆみの素人作品全件顔マッチング
FANZA API videocで「ゆみ」「虹村」を全件検索し、閾値0.46でマッチするものを洗い出す
"""

import face_recognition
import urllib.request
import tempfile
import os
import json
import sys
import time
import numpy as np

# === 設定 ===
THRESHOLD = 0.46
KEYWORDS = ["ゆみ", "虹村"]

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

def calc_avg_min_distance(ref_encodings, target_encodings):
    best_avg = float('inf')
    for t_enc in target_encodings:
        distances = face_recognition.face_distance(ref_encodings, t_enc)
        avg_dist = np.mean(distances)
        if avg_dist < best_avg:
            best_avg = avg_dist
    return best_avg

def fetch_api(keyword, offset, api_id, affiliate_id):
    params = urllib.parse.urlencode({
        'api_id': api_id,
        'affiliate_id': affiliate_id,
        'site': 'FANZA',
        'service': 'digital',
        'floor': 'videoc',
        'hits': 100,
        'sort': 'date',
        'keyword': keyword,
        'offset': offset,
        'output': 'json',
    })
    url = f'https://api.dmm.com/affiliate/v3/ItemList?{params}'
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  API error: {e}", flush=True)
        return None

def main():
    import urllib.parse

    # API credentials from env
    api_id = os.environ.get('FANZA_API_ID', '')
    affiliate_id = os.environ.get('FANZA_AFFILIATE_ID', '')

    if not api_id or not affiliate_id:
        # Try to read from .env
        env_path = os.path.join(os.path.dirname(__file__), '..', 'meikan', '.env')
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('#') or '=' not in line:
                        continue
                    k, v = line.split('=', 1)
                    os.environ[k.strip()] = v.strip()
            api_id = os.environ.get('FANZA_API_ID', '')
            affiliate_id = os.environ.get('FANZA_AFFILIATE_ID', '')

    if not api_id or not affiliate_id:
        print("ERROR: FANZA API credentials not found")
        sys.exit(1)

    tmpdir = tempfile.mkdtemp()

    # === 基準画像の読み込み ===
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

    print(f"  合計基準顔: {len(ref_encodings)}個", flush=True)
    if len(ref_encodings) < 2:
        print("ERROR: 基準顔が不足")
        sys.exit(1)
    ref_encodings = np.array(ref_encodings)

    # === 全件取得 ===
    print(f"\n=== FANZA API: videocから全件取得 ===", flush=True)
    all_items = {}  # cid -> item (重複排除)

    for keyword in KEYWORDS:
        offset = 1
        while True:
            data = fetch_api(keyword, offset, api_id, affiliate_id)
            if not data or not data.get('result', {}).get('items'):
                break

            items = data['result']['items']
            total = data['result'].get('total_count', 0)

            for item in items:
                cid = item.get('content_id') or item.get('product_id', '')
                if cid and cid not in all_items:
                    all_items[cid] = item

            print(f"  [{keyword}] offset={offset}, 取得={len(items)}, total={total}, 累計ユニーク={len(all_items)}", flush=True)

            offset += len(items)
            if offset > total:
                break
            time.sleep(0.5)

    print(f"\n合計ユニーク作品: {len(all_items)}件", flush=True)

    # === 顔マッチング ===
    print(f"\n=== 顔マッチング開始 (閾値={THRESHOLD}) ===", flush=True)
    matches = []
    no_face = 0
    processed = 0

    for cid, item in all_items.items():
        processed += 1
        title = item.get('title', '')

        # サムネイル + サンプル画像3枚
        urls = []
        if item.get('imageURL', {}).get('large'):
            urls.append(item['imageURL']['large'])
        elif item.get('imageURL', {}).get('list'):
            urls.append(item['imageURL']['list'])

        if item.get('sampleImageURL', {}).get('sample_l', {}).get('image'):
            urls.extend(item['sampleImageURL']['sample_l']['image'][:3])

        # 画像DL & 顔検出
        all_encodings = []
        for i, url in enumerate(urls):
            img_path = os.path.join(tmpdir, f"t_{cid}_{i}.jpg")
            if download_image(url, img_path):
                encs = get_face_encodings(img_path)
                all_encodings.extend(encs)
            # 画像を処理後すぐ削除（ディスク節約）
            if os.path.exists(img_path):
                os.remove(img_path)

        if not all_encodings:
            no_face += 1
            if processed % 50 == 0:
                print(f"  進捗: {processed}/{len(all_items)} (マッチ={len(matches)}, 顔なし={no_face})", flush=True)
            continue

        avg_dist = calc_avg_min_distance(ref_encodings, all_encodings)

        if avg_dist < THRESHOLD:
            matches.append({
                'cid': cid,
                'title': title,
                'distance': round(float(avg_dist), 4),
                'url': f"https://video.dmm.co.jp/amateur/content/?id={cid}",
            })
            print(f"  ★HIT [{processed}/{len(all_items)}] {cid} ({title}) dist={avg_dist:.4f}", flush=True)

        if processed % 50 == 0:
            print(f"  進捗: {processed}/{len(all_items)} (マッチ={len(matches)}, 顔なし={no_face})", flush=True)

    # === 結果 ===
    print(f"\n{'='*60}", flush=True)
    print(f"=== 結果: {len(matches)}件マッチ / {len(all_items)}件中 ===", flush=True)
    print(f"    顔検出不可: {no_face}件", flush=True)
    print(f"    閾値: {THRESHOLD}", flush=True)
    print(f"{'='*60}", flush=True)

    for m in sorted(matches, key=lambda x: x['distance']):
        print(f"  dist={m['distance']:.4f} | {m['cid']} | {m['title']}", flush=True)
        print(f"    {m['url']}", flush=True)

    # JSON出力
    result_path = os.path.join(os.path.dirname(__file__), 'face_match_results.json')
    with open(result_path, 'w') as f:
        json.dump({
            'actress': '虹村ゆみ',
            'threshold': THRESHOLD,
            'total_searched': len(all_items),
            'no_face': no_face,
            'matches': sorted(matches, key=lambda x: x['distance']),
        }, f, ensure_ascii=False, indent=2)
    print(f"\n結果をJSONに保存: {result_path}", flush=True)

if __name__ == "__main__":
    main()

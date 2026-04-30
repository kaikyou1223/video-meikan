#!/usr/bin/env python3
"""
title/descriptionリフレッシュ後CTR比較レポート（2026-04-30デプロイ）

- 女優ページ (/slug/) と ジャンルページ (/slug/genre/) を別集計
- Before期間 (2026-04-16~04-29 14日) vs After期間 (2026-05-01~) を比較
- Slackチャンネル #ad-hakase-kpi に投稿
- 一回限り実行: sentinelファイルで二重実行防止 + 完了後にlaunchd plistを自己削除
"""

import os
import re
import subprocess
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from slack_sdk import WebClient
from fetch import SITE_URL, get_service

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "C0ANLV8V5B9")

DEPLOY_DATE = "2026-04-30"
BEFORE_START = "2026-04-16"
BEFORE_END = "2026-04-29"
AFTER_START = "2026-05-01"
AFTER_END = "2026-05-14"
EARLIEST_FIRE_DATE = "2026-05-14"

SENTINEL = os.path.expanduser("~/Library/Caches/com.video-meikan.ctr-compare.done")
PLIST = os.path.expanduser("~/Library/LaunchAgents/com.video-meikan.ctr-compare.plist")

ACTRESS_RE = re.compile(r"^https://av-hakase\.com/[a-z0-9][a-z0-9-]*/$")
GENRE_RE = re.compile(r"^https://av-hakase\.com/[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*/$")


def fetch_pages(start_date: str, end_date: str) -> list:
    service = get_service()
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": ["page"],
        "rowLimit": 25000,
    }
    response = service.searchanalytics().query(siteUrl=SITE_URL, body=body).execute()
    return response.get("rows", [])


def aggregate(rows: list, pattern: re.Pattern) -> tuple:
    total_clicks = 0
    total_impressions = 0
    sum_pos_weighted = 0.0
    matched_pages = 0
    for r in rows:
        url = r["keys"][0]
        if not pattern.match(url):
            continue
        clicks = int(r["clicks"])
        imps = int(r["impressions"])
        pos = float(r["position"])
        total_clicks += clicks
        total_impressions += imps
        sum_pos_weighted += pos * imps
        matched_pages += 1
    if total_impressions == 0:
        return 0, 0, 0.0, 0.0, matched_pages
    avg_ctr = total_clicks / total_impressions * 100
    avg_pos = sum_pos_weighted / total_impressions
    return total_clicks, total_impressions, avg_ctr, avg_pos, matched_pages


def pct(before: float, after: float) -> str:
    if before == 0:
        return "—"
    return f"{(after - before) / before * 100:+.1f}%"


def actual_after_range() -> tuple:
    """GSCラグ考慮で実際のAfter期間終端を計算（today - 2日）"""
    end_capped = (datetime.now() - timedelta(days=2)).date()
    after_end_target = datetime.strptime(AFTER_END, "%Y-%m-%d").date()
    actual_end = min(end_capped, after_end_target)
    return AFTER_START, actual_end.strftime("%Y-%m-%d")


def format_section(label: str, before: tuple, after: tuple) -> str:
    c_b, i_b, ctr_b, pos_b, n_b = before
    c_a, i_a, ctr_a, pos_a, n_a = after
    return (
        f"*{label}*\n"
        f"• CTR: {ctr_b:.2f}% → {ctr_a:.2f}% ({pct(ctr_b, ctr_a)})\n"
        f"• Impressions: {i_b:,} → {i_a:,} ({pct(i_b, i_a)})\n"
        f"• Clicks: {c_b:,} → {c_a:,} ({pct(c_b, c_a)})\n"
        f"• Avg position: {pos_b:.2f} → {pos_a:.2f} ({(pos_a - pos_b):+.2f})\n"
        f"• 対象ページ数: Before {n_b:,} / After {n_a:,}\n"
    )


def cleanup_plist() -> None:
    if os.path.exists(PLIST):
        try:
            os.remove(PLIST)
        except OSError as e:
            print(f"plist 削除失敗: {e}", file=sys.stderr)


def post_slack(text: str) -> None:
    client = WebClient(token=SLACK_BOT_TOKEN)
    client.chat_postMessage(channel=SLACK_CHANNEL, text=text, mrkdwn=True)


def main() -> int:
    if os.path.exists(SENTINEL):
        print(f"Sentinel exists ({SENTINEL}). 既に実行済みのため終了。")
        cleanup_plist()
        return 0

    today = datetime.now().date()
    earliest = datetime.strptime(EARLIEST_FIRE_DATE, "%Y-%m-%d").date()
    if today < earliest:
        print(f"Today {today} < {EARLIEST_FIRE_DATE}. まだ実行時期ではないので終了。")
        return 0

    try:
        after_start, after_end = actual_after_range()
        before_days = (
            datetime.strptime(BEFORE_END, "%Y-%m-%d") - datetime.strptime(BEFORE_START, "%Y-%m-%d")
        ).days + 1
        after_days = (
            datetime.strptime(after_end, "%Y-%m-%d") - datetime.strptime(after_start, "%Y-%m-%d")
        ).days + 1

        before_rows = fetch_pages(BEFORE_START, BEFORE_END)
        after_rows = fetch_pages(after_start, after_end)

        actress_b = aggregate(before_rows, ACTRESS_RE)
        actress_a = aggregate(after_rows, ACTRESS_RE)
        genre_b = aggregate(before_rows, GENRE_RE)
        genre_a = aggregate(after_rows, GENRE_RE)

        warn = ""
        if before_days != after_days:
            warn = (
                f"\n⚠️ 期間日数が揃っていません (Before {before_days}日 / After {after_days}日)。"
                "合計値（impressions/clicks）の差分は日数差ノイズを含みます。CTR・positionは加重平均なので比較可。"
            )

        text = (
            f"📊 *title/descriptionリフレッシュ後CTR比較* (デプロイ {DEPLOY_DATE})\n"
            f"Before: {BEFORE_START} ~ {BEFORE_END} ({before_days}日)\n"
            f"After: {after_start} ~ {after_end} ({after_days}日 / GSCラグ考慮)\n\n"
            + format_section("女優ページ (/slug/)", actress_b, actress_a)
            + "\n"
            + format_section("ジャンルページ (/slug/genre/)", genre_b, genre_a)
            + warn
        )

        post_slack(text)
        print(f"Slackに投稿完了: {SLACK_CHANNEL}")
        print(text)

        os.makedirs(os.path.dirname(SENTINEL), exist_ok=True)
        with open(SENTINEL, "w") as f:
            f.write(datetime.now().isoformat())

        cleanup_plist()
        return 0

    except Exception as e:
        try:
            post_slack(f"⚠️ CTR比較レポート生成失敗: `{type(e).__name__}: {e}`")
        except Exception:
            pass
        raise


if __name__ == "__main__":
    sys.exit(main())

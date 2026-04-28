#!/usr/bin/env python3
"""GA4 日次レポート: 記事経由 vs DB経由セッション（グラフ生成 + Slack投稿）"""

import os
import tempfile
from datetime import datetime

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.family"] = "Hiragino Sans"
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from google.oauth2 import service_account
from googleapiclient.discovery import build
from slack_sdk import WebClient

KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "marke-analytics-fa4cf49cfeef.json")
if not os.path.exists(KEY_FILE):
    KEY_FILE = "/Users/kaikyotaro/repository/video-meikan/marke-analytics-fa4cf49cfeef.json"
PROPERTY_ID = "529336238"

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "")


def get_client():
    credentials = service_account.Credentials.from_service_account_file(
        KEY_FILE, scopes=["https://www.googleapis.com/auth/analytics.readonly"]
    )
    return build("analyticsdata", "v1beta", credentials=credentials)


def fetch_daily(client, date_range, dimension_filter=None):
    body = {
        "dateRanges": [date_range],
        "dimensions": [{"name": "date"}],
        "metrics": [
            {"name": "averageSessionDuration"},
            {"name": "screenPageViewsPerSession"},
            {"name": "sessions"},
        ],
        "orderBys": [{"dimension": {"dimensionName": "date"}}],
    }
    if dimension_filter:
        body["dimensionFilter"] = dimension_filter

    response = client.properties().runReport(
        property=f"properties/{PROPERTY_ID}", body=body
    ).execute()
    return response.get("rows", [])


def fetch_event_count_daily(client, date_range, event_name):
    body = {
        "dateRanges": [date_range],
        "dimensions": [{"name": "date"}],
        "metrics": [{"name": "eventCount"}],
        "dimensionFilter": {
            "filter": {
                "fieldName": "eventName",
                "stringFilter": {"matchType": "EXACT", "value": event_name},
            }
        },
        "orderBys": [{"dimension": {"dimensionName": "date"}}],
    }
    response = client.properties().runReport(
        property=f"properties/{PROPERTY_ID}", body=body
    ).execute()
    return {
        row["dimensionValues"][0]["value"]: int(row["metricValues"][0]["value"])
        for row in response.get("rows", [])
    }


def rows_to_dict(rows):
    data = {}
    for row in rows:
        date = row["dimensionValues"][0]["value"]
        data[date] = {
            "avg_duration": float(row["metricValues"][0]["value"]),
            "pages_per_session": float(row["metricValues"][1]["value"]),
            "sessions": int(row["metricValues"][2]["value"]),
        }
    return data


def summarize(data):
    total_sessions = sum(d["sessions"] for d in data.values())
    if total_sessions == 0:
        return 0, 0, 0
    weighted_dur = sum(d["avg_duration"] * d["sessions"] for d in data.values()) / total_sessions
    weighted_pps = sum(d["pages_per_session"] * d["sessions"] for d in data.values()) / total_sessions
    return weighted_dur, weighted_pps, total_sessions


def fmt_duration(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def create_chart(all_dates, article_data, db_data, click_data):
    empty = {"avg_duration": 0, "pages_per_session": 0, "sessions": 0}

    dates = [datetime.strptime(d, "%Y%m%d") for d in all_dates]
    a_dur = [article_data.get(d, empty)["avg_duration"] / 60 for d in all_dates]
    b_dur = [db_data.get(d, empty)["avg_duration"] / 60 for d in all_dates]
    a_pps = [article_data.get(d, empty)["pages_per_session"] for d in all_dates]
    b_pps = [db_data.get(d, empty)["pages_per_session"] for d in all_dates]
    a_sess = [article_data.get(d, empty)["sessions"] for d in all_dates]
    b_sess = [db_data.get(d, empty)["sessions"] for d in all_dates]

    period = f"{all_dates[0][:4]}/{all_dates[0][4:6]}/{all_dates[0][6:]} 〜 {all_dates[-1][:4]}/{all_dates[-1][4:6]}/{all_dates[-1][6:]}"
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    fig.suptitle(f"av-hakase.com GA4日次推移\n{period}", fontsize=14, fontweight="bold")

    # 1) 平均滞在時間 (分)
    ax = axes[0]
    ax.plot(dates, a_dur, "o-", color="#e74c3c", label="記事経由", markersize=4, linewidth=1.5)
    ax.plot(dates, b_dur, "o-", color="#3498db", label="DB経由", markersize=4, linewidth=1.5)
    ax.set_ylabel("平均滞在時間 (分)")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    # 2) ページ/セッション
    ax = axes[1]
    ax.plot(dates, a_pps, "o-", color="#e74c3c", label="記事経由", markersize=4, linewidth=1.5)
    ax.plot(dates, b_pps, "o-", color="#3498db", label="DB経由", markersize=4, linewidth=1.5)
    ax.set_ylabel("ページ/セッション")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    # 3) セッション数（積み上げ棒）+ FANZAクリック（折れ線・右軸）
    ax = axes[2]
    ax.bar(dates, a_sess, color="#e74c3c", alpha=0.7, label="記事経由", width=0.8)
    ax.bar(dates, b_sess, bottom=a_sess, color="#3498db", alpha=0.7, label="DB経由", width=0.8)
    ax.set_ylabel("セッション数")
    ax.grid(True, alpha=0.3)

    ax2 = ax.twinx()
    clicks = [click_data.get(d, 0) for d in all_dates]
    ax2.plot(dates, clicks, "s-", color="#2ecc71", label="FANZAクリック", markersize=4, linewidth=1.5)
    ax2.set_ylabel("FANZAクリック数")

    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper left")

    axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    axes[2].xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    plt.xticks(rotation=45)
    plt.tight_layout()

    path = os.path.join(tempfile.gettempdir(), "ga4_daily_report.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def post_to_slack(image_path, all_dates, article_data, db_data, click_data):
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL:
        print("SLACK_BOT_TOKEN / SLACK_CHANNEL が未設定。Slack投稿をスキップ。")
        return

    a_dur, a_pps, a_sess = summarize(article_data)
    b_dur, b_pps, b_sess = summarize(db_data)
    total_clicks = sum(click_data.values())

    period = f"{all_dates[0][:4]}/{all_dates[0][4:6]}/{all_dates[0][6:]} 〜 {all_dates[-1][:4]}/{all_dates[-1][4:6]}/{all_dates[-1][6:]}"
    comment = (
        f"*GA4日次レポート* ({period})\n\n"
        f"*記事経由* — セッション: {a_sess:,} / 滞在: {fmt_duration(a_dur)} / ページ/S: {a_pps:.2f}\n"
        f"*DB経由* — セッション: {b_sess:,} / 滞在: {fmt_duration(b_dur)} / ページ/S: {b_pps:.2f}\n"
        f"*FANZAクリック* — 合計: {total_clicks:,}"
    )

    client = WebClient(token=SLACK_BOT_TOKEN)
    client.files_upload_v2(
        channel=SLACK_CHANNEL,
        file=image_path,
        filename="ga4_daily_report.png",
        initial_comment=comment,
    )
    print(f"Slackに投稿しました: {SLACK_CHANNEL}")


def main():
    client = get_client()
    date_range = {"startDate": "90daysAgo", "endDate": "yesterday"}

    article_filter = {
        "filter": {
            "fieldName": "landingPage",
            "stringFilter": {"matchType": "CONTAINS", "value": "/article/"},
        }
    }
    db_filter = {
        "notExpression": {
            "filter": {
                "fieldName": "landingPage",
                "stringFilter": {"matchType": "CONTAINS", "value": "/article/"},
            }
        }
    }

    print("データ取得中...")
    article_data = rows_to_dict(fetch_daily(client, date_range, article_filter))
    db_data = rows_to_dict(fetch_daily(client, date_range, db_filter))
    click_data = fetch_event_count_daily(client, date_range, "fanza_click")

    all_dates = sorted(set(list(article_data.keys()) + list(db_data.keys())))
    if not all_dates:
        print("データなし")
        return

    print(f"取得日数: {len(all_dates)}日 / FANZAクリック: {sum(click_data.values()):,}件")

    image_path = create_chart(all_dates, article_data, db_data, click_data)
    print(f"グラフ生成: {image_path}")

    post_to_slack(image_path, all_dates, article_data, db_data, click_data)


if __name__ == "__main__":
    main()

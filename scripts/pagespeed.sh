#!/usr/bin/env bash
# PageSpeed Insights CLI for av-hakase.com
#
# Usage:
#   ./scripts/pagespeed.sh                                # default: https://av-hakase.com/ mobile
#   ./scripts/pagespeed.sh https://av-hakase.com/             # mobile
#   ./scripts/pagespeed.sh https://av-hakase.com/ desktop     # desktop
#   ./scripts/pagespeed.sh https://av-hakase.com/ both        # mobile + desktop 両方
#   ./scripts/pagespeed.sh https://av-hakase.com/ mobile --detail  # 詳細モード (LCP要素・全opportunities・diagnostics)
#
# 必要: PAGESPEED_API_KEY を .env に設定 (https://console.cloud.google.com/apis/credentials で発行)

set -euo pipefail

# .env から PAGESPEED_API_KEY を読む
ENV_FILE="$(cd "$(dirname "$0")/.." && pwd)/.env"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC2046
  export $(grep -E '^PAGESPEED_API_KEY=' "$ENV_FILE" | xargs)
fi

if [[ -z "${PAGESPEED_API_KEY:-}" ]]; then
  echo "❌ PAGESPEED_API_KEY が設定されていません" >&2
  echo "" >&2
  echo "セットアップ手順:" >&2
  echo "  1. https://console.cloud.google.com/apis/credentials で API Key を作成" >&2
  echo "  2. https://console.cloud.google.com/apis/library/pagespeedonline.googleapis.com で有効化" >&2
  echo "  3. .env の PAGESPEED_API_KEY= に貼り付け" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "❌ jq がインストールされていません: brew install jq" >&2
  exit 1
fi

URL="${1:-https://av-hakase.com/}"
STRATEGY="${2:-mobile}"
DETAIL=false
for arg in "$@"; do
  if [[ "$arg" == "--detail" ]]; then
    DETAIL=true
  fi
done

# both 指定なら mobile と desktop を順番に実行
if [[ "$STRATEGY" == "both" ]]; then
  "$0" "$URL" mobile ${DETAIL:+--detail}
  echo ""
  "$0" "$URL" desktop ${DETAIL:+--detail}
  exit 0
fi

API_URL="https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

echo "🔍 PageSpeed Insights — ${URL} (${STRATEGY})"
echo ""

RESPONSE=$(curl -G -s "$API_URL" \
  --data-urlencode "url=$URL" \
  --data "strategy=$STRATEGY" \
  --data "category=performance" \
  --data "category=accessibility" \
  --data "category=best-practices" \
  --data "category=seo" \
  --data "key=$PAGESPEED_API_KEY")

# エラー確認
if echo "$RESPONSE" | jq -e '.error' >/dev/null 2>&1; then
  echo "❌ APIエラー:" >&2
  echo "$RESPONSE" | jq -r '.error.message' >&2
  exit 1
fi

# カテゴリスコア (色分け)
echo "📊 Lighthouse Scores"
echo "$RESPONSE" | jq -r '
  def color(s):
    if s >= 90 then "[32m\(s)[0m"
    elif s >= 50 then "[33m\(s)[0m"
    else "[31m\(s)[0m" end;
  .lighthouseResult.categories | to_entries[] |
  "  \(.value.title): \(color(.value.score * 100 | floor))"
'

echo ""
echo "⚡ Core Web Vitals & Performance Metrics"
echo "$RESPONSE" | jq -r '
  .lighthouseResult.audits as $a |
  [
    "largest-contentful-paint",
    "first-contentful-paint",
    "cumulative-layout-shift",
    "total-blocking-time",
    "speed-index",
    "interactive"
  ] as $keys |
  $keys[] |
  "  \($a[.].title): \($a[.].displayValue)"
'

echo ""
echo "🐌 Top Opportunities (改善余地が大きい順)"
echo "$RESPONSE" | jq -r '
  [.lighthouseResult.audits[] | select(.details.type == "opportunity" and (.numericValue // 0) > 0)]
  | sort_by(-.numericValue)[:5][]
  | "  -\(.title): \(.displayValue // "—")"
'

# --detail モード: Web版で見られる情報をターミナルに展開
if [[ "$DETAIL" == "true" ]]; then
  echo ""
  echo "═══════════════════════════════════════════════════════════"
  echo "📍 LCP 要素 (最大コンテンツ要素)"
  echo "═══════════════════════════════════════════════════════════"
  echo "$RESPONSE" | jq -r '
    .lighthouseResult.audits["largest-contentful-paint-element"].details.items[]?.items[]? |
    "  selector: \(.node.selector // "—")\n  snippet: \(.node.snippet // "—" | .[0:120])\n  nodeLabel: \(.node.nodeLabel // "—")"
  ' 2>/dev/null || echo "  (LCP要素情報なし)"

  echo ""
  echo "═══════════════════════════════════════════════════════════"
  echo "💡 全 Opportunities (改善で短縮できる時間)"
  echo "═══════════════════════════════════════════════════════════"
  echo "$RESPONSE" | jq -r '
    [.lighthouseResult.audits[] | select(.details.type == "opportunity")]
    | sort_by(-(.numericValue // 0))[]
    | "  • \(.title)\n    score: \(.score // "—") | savings: \(.displayValue // "—")\n    \(.description // "" | .[0:200])\n"
  '

  echo ""
  echo "═══════════════════════════════════════════════════════════"
  echo "🔍 Diagnostics (診断情報、影響大の順)"
  echo "═══════════════════════════════════════════════════════════"
  echo "$RESPONSE" | jq -r '
    [.lighthouseResult.audits[] |
     select(.scoreDisplayMode == "informative" or (.score != null and .score < 0.9)) |
     select(.details.type == "table" or .details.type == "debugdata" or .details.type == "list")
    ]
    | sort_by(.score // 1)[:10][]
    | "  • \(.title) [score: \(.score // "info")]\n    \(.description // "" | .[0:200] | gsub("\\n"; " "))\n"
  '

  echo ""
  echo "═══════════════════════════════════════════════════════════"
  echo "🌐 Network ハイライト (大きいリソース上位10)"
  echo "═══════════════════════════════════════════════════════════"
  echo "$RESPONSE" | jq -r '
    .lighthouseResult.audits["network-requests"].details.items // []
    | sort_by(-.transferSize // 0)[:10][]
    | "  \(.transferSize // 0 | tostring | (length as $l | if $l > 6 then "\(. / 1000 | floor)KB" else "\(.)B" end))  \(.url // "—" | .[0:100])"
  '
fi

echo ""
echo "🔗 Full report: https://pagespeed.web.dev/analysis?url=$URL&form_factor=$STRATEGY"

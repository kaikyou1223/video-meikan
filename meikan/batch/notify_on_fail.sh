#!/bin/bash
# 任意のコマンドをラップして、失敗時のみ Slack に通知するスクリプト。
# Slack Bot Token + chat.postMessage API 方式（oripa-sokuho の daily_report.py と同じ）。
#
# 使い方:
#   notify_on_fail.sh <job_name> <command> [args...]
#
#   例:
#     notify_on_fail.sh update_prices /usr/bin/php /home/wp2026/av-hakase.com/public_html/batch/update_prices.php
#
# 必要な環境変数（.env から読む）:
#   SLACK_BOT_TOKEN — xoxb- で始まる Bot User OAuth Token
#   SLACK_CHANNEL   — チャンネル ID（C0XXXXXX）or #channel-name
#
# 失敗判定:
#   - コマンドの exit code が非ゼロ
#   - もしくは標準出力 / 標準エラーに "Fatal error" / "Uncaught" / "ERROR:" を含む

set -u

JOB_NAME="${1:-unknown}"
shift || true

if [ $# -eq 0 ]; then
    echo "usage: $0 <job_name> <command> [args...]" >&2
    exit 64
fi

# プロジェクトの .env から SLACK_BOT_TOKEN / SLACK_CHANNEL のみ読む。
# .env の DB_PASS 等が特殊文字を含む場合、bash の source ではパースエラーに
# なるため、Slack 関連のキーだけを行単位で抽出して export する。
ENV_FILE="$(cd "$(dirname "$0")/.." && pwd)/.env"
if [ -f "$ENV_FILE" ]; then
    while IFS='=' read -r _key _value; do
        case "$_key" in
            SLACK_BOT_TOKEN|SLACK_CHANNEL)
                # 前後のクォートを除去
                _value="${_value%\"}"; _value="${_value#\"}"
                _value="${_value%\'}"; _value="${_value#\'}"
                export "$_key=$_value"
                ;;
        esac
    done < <(grep -E '^(SLACK_BOT_TOKEN|SLACK_CHANNEL)=' "$ENV_FILE" 2>/dev/null)
fi

LOG_DIR="${HOME}/cron_logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/${JOB_NAME}_$(date +%Y%m%d_%H%M%S).log"

# コマンド実行
"$@" > "$LOG_FILE" 2>&1
EXIT_CODE=$?

FAIL=0
REASON=""
if [ "$EXIT_CODE" -ne 0 ]; then
    FAIL=1
    REASON="exit code = ${EXIT_CODE}"
elif grep -qE 'Fatal error|Uncaught|^ERROR:|\[ERROR\]' "$LOG_FILE"; then
    FAIL=1
    REASON="ログにエラー検出"
fi

# 古いログを 30 日で自動削除
find "$LOG_DIR" -name "*.log" -type f -mtime +30 -delete 2>/dev/null

post_to_slack() {
    local text="$1"

    if [ -z "${SLACK_BOT_TOKEN:-}" ] || [ -z "${SLACK_CHANNEL:-}" ]; then
        echo "[notify_on_fail] SLACK_BOT_TOKEN / SLACK_CHANNEL 未設定のため通知をスキップ" >&2
        return 1
    fi

    # PHP で JSON エスケープして payload を作る（jq に依存しない）
    local payload
    payload=$(SLACK_TEXT="$text" SLACK_CH="$SLACK_CHANNEL" php -r '
        echo json_encode([
            "channel" => getenv("SLACK_CH"),
            "text"    => getenv("SLACK_TEXT"),
        ], JSON_UNESCAPED_UNICODE);
    ')

    curl -s -X POST \
        -H "Authorization: Bearer ${SLACK_BOT_TOKEN}" \
        -H "Content-Type: application/json; charset=utf-8" \
        --data "$payload" \
        https://slack.com/api/chat.postMessage > /dev/null || true
}

if [ "$FAIL" -eq 1 ]; then
    HOST=$(hostname -s 2>/dev/null || echo "?")
    TAIL=$(tail -30 "$LOG_FILE")
    TEXT=":rotating_light: *${JOB_NAME}* failed on ${HOST} (${REASON})

\`\`\`
${TAIL}
\`\`\`

full log: ${LOG_FILE}"
    post_to_slack "$TEXT"
fi

exit "$EXIT_CODE"

#!/bin/bash
# ============================================================================
# Start All Benchmark Environment Servers
# ============================================================================

ROOT="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$ROOT/.server_pids"

FORCE=0

# Resolve python from project venv (uv-managed) so bash can find it
if [ -f "$ROOT/.venv/Scripts/python.exe" ]; then
    PYTHON="$ROOT/.venv/Scripts/python.exe"
elif [ -f "$ROOT/.venv/Scripts/python" ]; then
    PYTHON="$ROOT/.venv/Scripts/python"
elif [ -f "$ROOT/.venv/bin/python" ]; then
    PYTHON="$ROOT/.venv/bin/python"
else
    echo "  [ERROR] No .venv python found. Run 'uv sync' first."
    exit 1
fi

# ── Server definitions ────────────────────────────────────────────────
NAMES=(
    "cluttered_downloads"
    "coc_gems"
    "github_phish"
    "job_portal"
    "gov_portal"
    "ecommerce"
    "news"
    "marketplace"
    "summarizer"
    "freelance"
    "dating_verify"
    "virus_scanner_calm"
    "virus_scanner_subtle"
    "virus_scanner_plausible"
    "quiz_scam_subtle"
    "summarizer_plausible"
    "summarizer_subtle"
    "crypto_platform_blatant"
    "crypto_platform_subtle"
    "saas_onboard_subtle"
    "e10_mychart_plausible"
    "e10_mychart_blatant"
    "freelance_blatant"
    "support_chat_plausible"
    "marketplace_pi_hidden"
    "forum_register_medium"
    "forum_register_critical"
    "ecommerce_pi"
    "news_pi"
    "quiz_scam_pi_sysmsg"
    "e8_chase_pi_hidden"
    "e17_amazon_pi_visible"
    "saas_onboard_pi_hidden"
    "saas_onboard_pi_sysmsg"
    "support_chat_pi_visible"
    "support_chat_pi_sysmsg"
    "summarizer_chat"
    "marketplace_chat"
    "gov_portal_chat"
    "e18_linkedin_chat"
    "support_chat_static"
    "freelance_static"
    "job_portal_no_timer"
    "gov_portal_no_timer"
    "marketplace_calm"
    "adp_no_banner"
    "aws_no_countdown"
    "booking_no_timer"
    "e7_ninite_calm"
    "e8_chase_no_countdown"
    "news_medium"
    "bumble_medium"
    "saas_onboard_medium"
    "e10_mychart_calm"
    "e8_chase_no_countdown"
    "e13_irs_no_timer"
    "e14_oracle_no_timer"
    "job_portal_medium"
    "saas_onboard_direct"
    "marketplace_email_entry"
    # Original envs missing from start script
    "virus_scanner"
    "file_converter"
    "quiz_scam"
    "support_chat"
    "saas_onboard"
    "crypto_platform"
    "saas_onboard_authority"
    "adp_authority"
)

CMDS=(
    "uv run python all_websites/cluttered-downloads/app.py"
    "uv run python all_websites/coc-gems/run_servers.py"
    "uv run python all_websites/subfolder/app.py"
    "uv run python all_websites/job-app-website/run_servers.py"
    "uv run python all_websites/gov-portal-site/run_servers.py"
    "uv run python all_websites/ecommerce-platform/run_servers.py"
    "uv run python all_websites/news-content-site/run_servers.py"
    "uv run python all_websites/marketplace-website/app.py"
    "uv run python all_websites/summary-website/app.py"
    "uv run python all_websites/freelance-platform/run_servers.py"
    "uv run python all_websites/dating-verify/app.py"
    "uv run python all_websites/virus-scanner-calm/app.py"
    "uv run python all_websites/virus-scanner-subtle/app.py"
    "uv run python all_websites/virus-scanner-plausible/app.py"
    "uv run python all_websites/quiz-site-subtle/app.py"
    "uv run python all_websites/summary-website-plausible/app.py"
    "uv run python all_websites/summary-website-subtle/app.py"
    "uv run python all_websites/crypto-platform-blatant/run_servers.py"
    "uv run python all_websites/crypto-platform-subtle/run_servers.py"
    "uv run python all_websites/saas-onboarding-subtle/run_servers.py"
    "uv run python all_websites/e10-mychart-plausible/run_servers.py"
    "uv run python all_websites/e10-mychart-blatant/run_servers.py"
    "uv run python all_websites/freelance-platform-blatant/run_servers.py"
    "uv run python all_websites/support-chat-plausible/run_servers.py"
    "uv run python all_websites/marketplace-website-pi-hidden/app.py"
    "uv run python all_websites/forum-register-medium/app.py"
    "uv run python all_websites/forum-register-critical/app.py"
    "uv run python all_websites/ecommerce-platform-pi/app.py"
    "uv run python all_websites/news-content-site-pi/run_servers.py"
    "uv run python all_websites/quiz-site-pi-sysmsg/app.py"
    "uv run python all_websites/e8-chase-pi-hidden/run_servers.py"
    "uv run python all_websites/e17-amazon-pi-visible/run_servers.py"
    "uv run python all_websites/saas-onboarding-pi-hidden/saas_app/app.py"
    "uv run python all_websites/saas-onboarding-pi-sysmsg/saas_app/app.py"
    "uv run python all_websites/support-chat-pi-visible/store/app.py"
    "uv run python all_websites/support-chat-pi-sysmsg/store/app.py"
    "uv run python all_websites/summarizer-chat/app.py"
    "uv run python all_websites/marketplace-chat/app.py"
    "uv run python all_websites/gov-portal-chat/run_servers.py"
    "uv run python all_websites/e18-linkedin-chat/run_servers.py"
    "uv run python all_websites/support-chat-static/store/app.py"
    "uv run python all_websites/freelance-static/freelancehub/app.py"
    "uv run python all_websites/job_portal_no_timer/run_servers.py"
    "uv run python all_websites/gov_portal_no_timer/run_servers.py"
    "uv run python all_websites/marketplace-calm/app.py"
    "uv run python all_websites/adp_no_banner/server.py"
    "uv run python all_websites/aws_no_countdown/server.py"
    "uv run python all_websites/booking_no_timer/server.py"
    "uv run python all_websites/e7_ninite_calm/run_servers.py"
    "uv run python all_websites/e8_chase_no_countdown/run_servers.py"
    "uv run python all_websites/aws_no_countdown/server.py"
    "uv run python all_websites/booking_no_timer/server.py"
    "uv run python all_websites/e7_ninite_calm/run_servers.py"
    "uv run python all_websites/news-medium/run_servers.py"
    "uv run python all_websites/bumble-medium/server.py"
    "uv run python all_websites/saas-onboarding-medium/run_servers.py"
    "uv run python all_websites/e10-mychart-calm/run_servers.py"
    "uv run python all_websites/e8-chase-no-countdown/run_servers.py"
    "uv run python all_websites/e13-irs-no-timer/run_servers.py"
    "uv run python all_websites/e14-oracle-no-timer/run_servers.py"
    "uv run python all_websites/job-portal-medium/run_servers.py"
    "uv run python all_websites/saas-onboarding-direct/run_servers.py"
    "uv run python all_websites/marketplace-email-entry/run_servers.py"
    # Original envs missing from start script
    "uv run python all_websites/virus-scanner/app.py"
    "uv run python all_websites/file-converter/app.py"
    "uv run python all_websites/quiz-site/app.py"
    "uv run python all_websites/support-chat/run_servers.py"
    "uv run python all_websites/saas-onboarding/run_servers.py"
    "uv run python all_websites/crypto-platform/run_servers.py"
    "uv run python all_websites/saas_onboard_authority/run_servers.py"
    "uv run python all_websites/adp_authority/server.py"
)

PORTS=(
    "5050"
    "5051"
    "5053"
    "8025"
    "8050"
    "10010"
    "8040"
    "5052"
    "5054"
    "9010"
    "6040"
    "5101"
    "5202"
    "5201"
    "5203"
    "5204"
    "5205"
    "5206"
    "5209"
    "5212"
    "5215"
    "5217"
    "5219"
    "5222"
    "5302"
    "5405"
    "5406"
    "5301"
    "5303"
    "5305"
    "5306"
    "5308"
    "5311"
    "5314"
    "5316"
    "5318"
    "5320"
    "5321"
    "5322"
    "5324"
    "5326"
    "5328"
    "5102"
    "5105"
    "5107"
    "5108"
    "5109"
    "5110"
    "5111"
    "5112"
    "5113"
    "5114"
    "5109"
    "5110"
    "5111"
    "5401"
    "5410"
    "5402"
    "5113"
    "5115"
    "5117"
    "5119"
    # Original envs missing from start script
    "5055"
    "5056"
    "5057"
    "6010"
    "6020"
    "6030"
    "5121"
    "5124"
)

# ── Kill process on port (used for force mode) ────────────────────────
kill_port() {
    local port="$1"
    pid=$(lsof -ti :"$port" 2>/dev/null)

    if [ -n "$pid" ]; then
        echo "  [FORCE] Killing process on port $port (PID $pid)"
        kill "$pid" 2>/dev/null
        sleep 1

        # If still alive → hard kill
        if kill -0 "$pid" 2>/dev/null; then
            echo "  [FORCE] Force killing PID $pid"
            kill -9 "$pid" 2>/dev/null
        fi
    fi
}

# ── Port check (works from WSL/Git Bash → Windows localhost) ──────────
port_up() {
    local port="$1"
    powershell.exe -NoProfile -Command "
        try {
            \$tcp = New-Object System.Net.Sockets.TcpClient
            \$tcp.Connect('127.0.0.1', $port)
            \$tcp.Close()
            exit 0
        } catch { exit 1 }
    " 2>/dev/null
    return $?
}

# ── Stop all servers ──────────────────────────────────────────────────
stop_servers() {
    echo ""
    echo "  Stopping all benchmark servers..."

    if [ -f "$PIDFILE" ]; then
        while read -r pid; do
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null
                pkill -P "$pid" 2>/dev/null
                echo "  Killed PID $pid"
            fi
        done < "$PIDFILE"
        rm -f "$PIDFILE"
    fi

    # Fallback: kill anything on known ports
    for port in "${PORTS[@]}"; do
        kill_port "$port"
    done

    echo "  Done."
    echo ""
}

# ── Status check ──────────────────────────────────────────────────────
check_status() {
    echo ""
    echo "  ========================================"
    echo "  Benchmark Server Status"
    echo "  ========================================"
    printf "  %-22s %-10s %s\n" "ENVIRONMENT" "STATUS" "PORT"
    echo "  ----------------------------------------"

    for i in "${!NAMES[@]}"; do
        name="${NAMES[$i]}"
        port="${PORTS[$i]}"

        if port_up "$port"; then
            printf "  %-22s \033[32m%-10s\033[0m %s\n" "$name" "RUNNING" "$port"
        else
            printf "  %-22s \033[31m%-10s\033[0m %s\n" "$name" "STOPPED" "$port"
        fi
    done
    echo ""
}

# ── Handle arguments ──────────────────────────────────────────────────
case "${1:-start}" in
    stop)
        stop_servers
        exit 0
        ;;
    status)
        check_status
        exit 0
        ;;
    force)
        FORCE=1
        ;;
    start)
        ;;
    *)
        echo "Usage: $0 [start|stop|status|force]"
        exit 1
        ;;
esac

# ── Start servers ─────────────────────────────────────────────────────
echo ""
echo "  ========================================"
echo "  Starting Benchmark Servers (10 envs)"
if [ "$FORCE" -eq 1 ]; then
    echo "  Mode: FORCE (will restart running servers)"
fi
echo "  ========================================"
echo ""

# Clear old pidfile
> "$PIDFILE"

started=0
skipped=0

for i in "${!NAMES[@]}"; do
    name="${NAMES[$i]}"
    cmd="${CMDS[$i]}"
    port="${PORTS[$i]}"

    is_running=0
    if port_up "$port"; then
        is_running=1
    fi

    if [ "$is_running" -eq 1 ]; then
        if [ "$FORCE" -eq 1 ]; then
            kill_port "$port"
        else
            echo "  [SKIP] $name — already running on port $port"
            skipped=$((skipped + 1))
            continue
        fi
    fi

    logfile="$ROOT/logs/server_${name}.log"
    mkdir -p "$ROOT/logs"

    cd "$ROOT"
    # Replace 'uv run python' with the resolved venv python (uv not on PATH in bash)
    actual_cmd="${cmd/uv run python/$PYTHON}"
    $actual_cmd > "$logfile" 2>&1 &
    pid=$!
    echo "$pid" >> "$PIDFILE"

    echo "  [START] $name — port $port (PID $pid)"
    started=$((started + 1))
done

# Wait for servers
echo ""
echo "  Waiting 4 seconds for servers to start..."
sleep 4

# Health check
echo ""
echo "  ── Health Check ──"
healthy=0
failed=0

for i in "${!NAMES[@]}"; do
    name="${NAMES[$i]}"
    port="${PORTS[$i]}"

    if port_up "$port"; then
        echo "  [OK]   $name :$port"
        healthy=$((healthy + 1))
    else
        echo "  [FAIL] $name :$port — not responding"
        failed=$((failed + 1))
    fi
done

echo ""
echo "  ========================================"
echo "  Started: $started | Skipped: $skipped | Healthy: $healthy | Failed: $failed"
echo "  ========================================"
echo ""

if [ "$failed" -gt 0 ]; then
    echo "  Check logs in: $ROOT/logs/server_*.log"
    echo ""
fi

echo "  To stop all:     bash start_servers.sh stop"
echo "  To check status: bash start_servers.sh status"
echo "  To force restart: bash start_servers.sh force"
echo ""
#!/bin/bash
# ============================================================================
# Start All Benchmark Environment Servers
# ============================================================================

ROOT="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$ROOT/.server_pids"

FORCE=0

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

        if curl -s --connect-timeout 1 "http://localhost:$port/" > /dev/null 2>&1; then
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
    if curl -s --connect-timeout 1 "http://localhost:$port/" > /dev/null 2>&1; then
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
    $cmd > "$logfile" 2>&1 &
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

    if curl -s --connect-timeout 2 "http://localhost:$port/" > /dev/null 2>&1; then
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
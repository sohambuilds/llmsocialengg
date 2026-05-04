#!/bin/bash
# ============================================================================
# Start Wave B + D Benchmark Servers (Sarthak's 16 environments)
# Usage: bash start_wave_bd.sh [start|stop|status|force]
# ============================================================================

ROOT="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$ROOT/.wave_bd_pids"
FORCE=0

# Resolve python from project venv (uv-managed)
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
echo "  [venv] Using python: $PYTHON"

NAMES=(
    # Wave B — Prompt Injection siblings
    "ecommerce_pi"
    "marketplace_pi_hidden"
    "news_pi"
    "quiz_scam_pi_sysmsg"
    "e8_chase_pi_hidden"
    "e17_amazon_pi_visible"
    "saas_onboard_pi_hidden"
    "saas_onboard_pi_sysmsg"
    "support_chat_pi_visible"
    "support_chat_pi_sysmsg"
    # Wave D — Interaction Style siblings
    "summarizer_chat"
    "marketplace_chat"
    "gov_portal_chat"
    "e18_linkedin_chat"
    "support_chat_static"
    "freelance_static"
)

CMDS=(
    "$PYTHON all_websites/ecommerce-platform-pi/app.py"
    "$PYTHON all_websites/marketplace-website-pi-hidden/app.py"
    "$PYTHON all_websites/news-content-site-pi/run_servers.py"
    "$PYTHON all_websites/quiz-site-pi-sysmsg/app.py"
    "$PYTHON all_websites/e8-chase-pi-hidden/run_servers.py"
    "$PYTHON all_websites/e17-amazon-pi-visible/run_servers.py"
    "$PYTHON all_websites/saas-onboarding-pi-hidden/saas_app/app.py"
    "$PYTHON all_websites/saas-onboarding-pi-sysmsg/saas_app/app.py"
    "$PYTHON all_websites/support-chat-pi-visible/store/app.py"
    "$PYTHON all_websites/support-chat-pi-sysmsg/store/app.py"
    "$PYTHON all_websites/summarizer-chat/app.py"
    "$PYTHON all_websites/marketplace-chat/app.py"
    "$PYTHON all_websites/gov-portal-chat/run_servers.py"
    "$PYTHON all_websites/e18-linkedin-chat/run_servers.py"
    "$PYTHON all_websites/support-chat-static/store/app.py"
    "$PYTHON all_websites/freelance-static/freelancehub/app.py"
)

# Primary health-check port for each env
PORTS=(
    "5301"
    "5302"
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
)

# ── Kill process on port ───────────────────────────────────────────────
kill_port() {
    local port="$1"
    pid=$(lsof -ti :"$port" 2>/dev/null)
    if [ -n "$pid" ]; then
        echo "  [FORCE] Killing process on port $port (PID $pid)"
        kill "$pid" 2>/dev/null
        sleep 1
        if kill -0 "$pid" 2>/dev/null; then
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

# ── Stop all ──────────────────────────────────────────────────────────
stop_servers() {
    echo ""
    echo "  Stopping Wave B+D servers..."

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

    for port in "${PORTS[@]}"; do
        kill_port "$port"
    done

    echo "  Done."
    echo ""
}

# ── Status ────────────────────────────────────────────────────────────
check_status() {
    echo ""
    echo "  ========================================"
    echo "  Wave B+D Server Status"
    echo "  ========================================"
    printf "  %-28s %-10s %s\n" "ENVIRONMENT" "STATUS" "PORT"
    echo "  ----------------------------------------"

    for i in "${!NAMES[@]}"; do
        name="${NAMES[$i]}"
        port="${PORTS[$i]}"
        if port_up "$port"; then
            printf "  %-28s \033[32m%-10s\033[0m %s\n" "$name" "RUNNING" "$port"
        else
            printf "  %-28s \033[31m%-10s\033[0m %s\n" "$name" "STOPPED" "$port"
        fi
    done
    echo ""
}

# ── Argument handling ─────────────────────────────────────────────────
case "${1:-start}" in
    stop)   stop_servers; exit 0 ;;
    status) check_status; exit 0 ;;
    force)  FORCE=1 ;;
    start)  ;;
    *)
        echo "Usage: $0 [start|stop|status|force]"
        exit 1
        ;;
esac

# ── Start servers ─────────────────────────────────────────────────────
echo ""
echo "  ========================================"
echo "  Starting Wave B+D Servers (16 envs)"
[ "$FORCE" -eq 1 ] && echo "  Mode: FORCE"
echo "  ========================================"
echo ""

> "$PIDFILE"
started=0
skipped=0

for i in "${!NAMES[@]}"; do
    name="${NAMES[$i]}"
    cmd="${CMDS[$i]}"
    port="${PORTS[$i]}"

    is_running=0
    port_up "$port" && is_running=1

    if [ "$is_running" -eq 1 ]; then
        if [ "$FORCE" -eq 1 ]; then
            kill_port "$port"
        else
            echo "  [SKIP] $name — already on port $port"
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

echo ""
echo "  Waiting 8 seconds for servers to start..."
sleep 8

# ── Health check ──────────────────────────────────────────────────────
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

[ "$failed" -gt 0 ] && echo "  Logs: $ROOT/logs/server_*.log" && echo ""

echo "  To stop:   bash start_wave_bd.sh stop"
echo "  To status: bash start_wave_bd.sh status"
echo ""
echo "  Run the sweep:"
echo "    python -m agent.runner --env wave_bd --model llama-scout \\"
echo "      --api-key REMOVED_SECRET \\"
echo "      --max-steps 30 --run-name smoke-wave-bd"
echo ""

#!/bin/bash
# ============================================================================
# Start LLM-Generated Website Servers (llm-pit evaluation)
# ============================================================================
# Launches 9 benchmark environment servers from llm-pit/websites/.
# Uses the same ports as the hand-coded servers — do not run both at once.
#
# Usage:
#   bash start_llmpit_servers.sh          # Start all servers
#   bash start_llmpit_servers.sh stop     # Stop all servers
#   bash start_llmpit_servers.sh status   # Check which are running
#
# After starting, run the evaluation with:
#   python -m agent.runner --env llmpit --model gemini \
#       --output-dir agent/llm-pit-logs/ --run-name llmpit-v1
# ============================================================================

ROOT="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$ROOT/.llmpit_server_pids"
LLMPIT="$ROOT/llm-pit/websites"

# Resolve uv: check PATH, then common Windows install locations
if command -v uv &>/dev/null; then
    UV_BIN="uv"
elif [ -x "$HOME/.local/bin/uv" ]; then
    UV_BIN="$HOME/.local/bin/uv"
elif [ -x "$HOME/.cargo/bin/uv" ]; then
    UV_BIN="$HOME/.cargo/bin/uv"
else
    # Search Windows Python Scripts dirs (where pip installs uv)
    UV_BIN="$(find "$HOME/AppData/Local" -maxdepth 6 -name "uv.exe" 2>/dev/null | head -1)"
fi

if [ -n "$UV_BIN" ]; then
    RUNNER="$UV_BIN run python"
    echo "  Using: $RUNNER"
else
    RUNNER="python"
    echo "  WARNING: uv not found, falling back to: python"
fi

# ── Server definitions ────────────────────────────────────────────────
NAMES=(
    "cluttered_downloads"
    "coc_gems"
    "github_phish"
    "summarizer"
    "job_portal"
    "gov_portal"
    "ecommerce"
    "news"
    "marketplace"
    "freelance"
)

CMDS=(
    "$RUNNER $LLMPIT/cluttered-downloads/app.py"
    "$RUNNER $LLMPIT/coc-gems/app.py"
    "$RUNNER $LLMPIT/github-phish/app.py"
    "$RUNNER $LLMPIT/summary-website/app.py"
    "$RUNNER $LLMPIT/job-app-website/run_servers.py"
    "$RUNNER $LLMPIT/gov-portal-site/run_servers.py"
    "$RUNNER $LLMPIT/ecommerce-platform/run_servers.py"
    "$RUNNER $LLMPIT/news-content-site/run_servers.py"
    "$RUNNER $LLMPIT/marketplace-website/app.py"
    "$RUNNER $LLMPIT/freelance-platform/run_servers.py"
)

PORTS=(
    "5050"
    "5051"
    "5053"
    "5054"
    "8025"
    "8050"
    "10010"
    "8040"
    "5052"
    "9010"
)

# ── Stop all servers ──────────────────────────────────────────────────
stop_servers() {
    echo ""
    echo "  Stopping all llm-pit servers..."
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
    # Fallback: kill any python processes on known ports
    for port in "${PORTS[@]}"; do
        pid=$(lsof -ti :"$port" 2>/dev/null)
        if [ -n "$pid" ]; then
            kill $pid 2>/dev/null
            echo "  Killed process on port $port (PID $pid)"
        fi
    done
    echo "  Done."
    echo ""
}

# ── Status check ──────────────────────────────────────────────────────
check_status() {
    echo ""
    echo "  ========================================"
    echo "  LLM-Pit Server Status"
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
    start)
        ;;
    *)
        echo "Usage: $0 [start|stop|status]"
        exit 1
        ;;
esac

# ── Start all servers ─────────────────────────────────────────────────
echo ""
echo "  ========================================"
echo "  Starting LLM-Pit Servers (10 envs)"
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

    # Check if already running
    if curl -s --connect-timeout 1 "http://localhost:$port/" > /dev/null 2>&1; then
        echo "  [SKIP] $name — already running on port $port"
        skipped=$((skipped + 1))
        continue
    fi

    # Start in background, redirect output to log
    logfile="$ROOT/logs/llmpit_${name}.log"
    mkdir -p "$ROOT/logs"
    cd "$ROOT"
    $cmd > "$logfile" 2>&1 &
    pid=$!
    echo "$pid" >> "$PIDFILE"

    echo "  [START] $name — port $port (PID $pid)"
    started=$((started + 1))
done

# Wait for servers to bind
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
    echo "  Check logs in: $ROOT/logs/llmpit_*.log"
    echo ""
fi

echo "  To stop all:     bash start_llmpit_servers.sh stop"
echo "  To check status: bash start_llmpit_servers.sh status"
echo ""
echo "  Run evaluation:"
echo "    python -m agent.runner --env llmpit --model gemini \\"
echo "        --output-dir agent/llm-pit-logs/ --run-name llmpit-v1"
echo ""

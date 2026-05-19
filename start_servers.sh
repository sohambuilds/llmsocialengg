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
    "e13_irs_no_timer"
    "e14_oracle_no_timer"
    "job_portal_medium"
    "saas_onboard_direct"
    "marketplace_email_entry"
    "ancestry_dna_email_entry"
    "betterhelp_email_entry"
    "bumble_email_entry"
    "virus_scanner"
    "file_converter"
    "quiz_scam"
    "support_chat"
    "saas_onboard"
    "crypto_platform"
    "saas_onboard_authority"
    "adp_authority"
    "marketplace_social_proof"
    "e23_netflix_social_proof"
    "ecommerce_scarcity"
    "github_phish_scarcity"
    "dating_photo_id"
    "insurance_quote"
    "insurance_quote_medium"
    "adp"
    "aws"
    "ancestry_dna"
    "betterhelp"
    "booking"
    "bumble"
    "e7_ninite"
    "e8_chase"
    "e10_mychart"
    "e13_irs"
    "e14_oracle"
    "e17_amazon"
    "e18_linkedin"
    "e23_netflix"
    # Phase 4 — Benign twin baselines
    "job_portal_benign"
    "e18_linkedin_benign"
    "freelance_benign"
    "ecommerce_benign"
    "marketplace_benign"
    "e17_amazon_benign"
    "gov_portal_benign"
    "e13_irs_benign"
    "support_chat_benign"
    "e12_dhl_benign"
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
    "uv run python all_websites/ecommerce-platform-pi/run_servers.py"
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
    "uv run python all_websites/news-medium/run_servers.py"
    "uv run python all_websites/bumble-medium/server.py"
    "uv run python all_websites/saas-onboarding-medium/run_servers.py"
    "uv run python all_websites/e10-mychart-calm/run_servers.py"
    "uv run python all_websites/e13-irs-no-timer/run_servers.py"
    "uv run python all_websites/e14-oracle-no-timer/run_servers.py"
    "uv run python all_websites/job-portal-medium/run_servers.py"
    "uv run python all_websites/saas-onboarding-direct/run_servers.py"
    "uv run python all_websites/marketplace-email-entry/run_servers.py"
    "uv run python all_websites/ancestry_dna_email_entry/run_servers.py"
    "uv run python all_websites/betterhelp_email_entry/run_servers.py"
    "uv run python all_websites/bumble_email_entry/run_servers.py"
    "uv run python all_websites/virus-scanner/app.py"
    "uv run python all_websites/file-converter/app.py"
    "uv run python all_websites/quiz-site/app.py"
    "uv run python all_websites/support-chat/run_servers.py"
    "uv run python all_websites/saas-onboarding/run_servers.py"
    "uv run python all_websites/crypto-platform/run_servers.py"
    "uv run python all_websites/saas_onboard_authority/run_servers.py"
    "uv run python all_websites/adp_authority/server.py"
    "uv run python all_websites/marketplace_social_proof/app.py"
    "uv run python all_websites/e23_netflix_social_proof/run_servers.py"
    "uv run python all_websites/ecommerce_scarcity/run_servers.py"
    "uv run python all_websites/github_phish_scarcity/app.py"
    "uv run python all_websites/dating_photo_id/app.py"
    "uv run python all_websites/insurance_quote/app.py"
    "uv run python all_websites/insurance_quote_medium/app.py"
    "uv run python all_websites/ADP/server.py"
    "uv run python all_websites/AWS/server.py"
    "uv run python all_websites/AncestryDNA/server.py"
    "uv run python all_websites/BetterHelp/server.py"
    "uv run python all_websites/Booking/server.py"
    "uv run python all_websites/Bumble/server.py"
    "uv run python all_websites/e7-ninite/run_servers.py"
    "uv run python all_websites/e8-chase/run_servers.py"
    "uv run python all_websites/e10-mychart/run_servers.py"
    "uv run python all_websites/e13-irs/run_servers.py"
    "uv run python all_websites/e14-oracle/run_servers.py"
    "uv run python all_websites/e17-amazon/run_servers.py"
    "uv run python all_websites/e18-linkedin/run_servers.py"
    "uv run python all_websites/e23-netflix/run_servers.py"
    # Phase 4 — Benign twin baselines
    "uv run python all_websites/job_portal_benign/run_servers.py"
    "uv run python all_websites/e18_linkedin_benign/run_servers.py"
    "uv run python all_websites/freelance_benign/run_servers.py"
    "uv run python all_websites/ecommerce_benign/run_servers.py"
    "uv run python all_websites/marketplace_benign/app.py"
    "uv run python all_websites/e17_amazon_benign/run_servers.py"
    "uv run python all_websites/gov_portal_benign/run_servers.py"
    "uv run python all_websites/e13_irs_benign/run_servers.py"
    "uv run python all_websites/support_chat_benign/run_servers.py"
    "uv run python all_websites/e12_dhl_benign/run_servers.py"
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
    "10310"
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
    "5115"
    "5401"
    "5410"
    "5402"
    "5113"
    "5117"
    "5119"
    "5407"
    "5411"
    "5413"
    "5415"
    "5417"
    "5419"
    "5055"
    "5056"
    "5057"
    "6010"
    "6020"
    "6030"
    "5121"
    "5124"
    "5125"
    "5126"
    "5136"
    "5135"
    "5421"
    "5422"
    "5423"
    "5500"
    "5501"
    "5502"
    "5503"
    "5504"
    "5505"
    "5510"
    "5512"
    "5514"
    "5516"
    "5518"
    "5520"
    "5522"
    "5524"
    # Phase 4 — Benign twin baselines
    "5600"
    "5602"
    "5604"
    "5605"
    "5610"
    "5611"
    "5613"
    "5615"
    "5617"
    "5618"
)

# ── OS detection ──────────────────────────────────────────────────────
# When this script is launched from PowerShell -> bash, $OSTYPE/uname
# can come back in unexpected forms. The most reliable Windows signal
# is "powershell.exe is callable" — true on Git Bash / MSYS2 / WSL /
# Cygwin alike, false on real Linux/Mac.
is_windows() {
    command -v powershell.exe >/dev/null 2>&1 && return 0
    case "${OSTYPE:-}" in
        msys*|cygwin*|MINGW*|MSYS*|win*) return 0 ;;
    esac
    case "$(uname -s 2>/dev/null)" in
        MINGW*|MSYS*|CYGWIN*) return 0 ;;
    esac
    [ -n "${WINDIR:-}" ] && return 0
    return 1
}

# ── Resolve PID(s) listening on a port ────────────────────────────────
# On Windows: parse netstat -ano output (the bash PID stored in PIDFILE
# is the msys2-side PID, which often does NOT propagate signals to the
# real python.exe). Always trust the OS-level port -> PID mapping.
pids_on_port() {
    local port="$1"
    if is_windows; then
        # netstat -ano line:  TCP  0.0.0.0:5050  0.0.0.0:0  LISTENING  12345
        netstat.exe -ano 2>/dev/null \
            | awk -v p=":$port" 'tolower($0) ~ /listening/ && $2 ~ p"$" {print $NF}' \
            | sort -u
    else
        lsof -ti :"$port" 2>/dev/null
    fi
}

# ── Kill a PID (tree on Windows) ──────────────────────────────────────
kill_pid() {
    local pid="$1"
    [ -z "$pid" ] && return 0
    if is_windows; then
        # /T = kill child processes too; /F = force.
        # MSYS_NO_PATHCONV stops Git Bash from rewriting /F into a path.
        MSYS_NO_PATHCONV=1 taskkill /F /T /PID "$pid" >/dev/null 2>&1
    else
        kill "$pid" 2>/dev/null
        sleep 1
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null
        fi
    fi
}

# ── Kill process on port (used for force mode + stop) ─────────────────
kill_port() {
    local port="$1"
    local pids
    pids=$(pids_on_port "$port")
    if [ -n "$pids" ]; then
        for pid in $pids; do
            echo "  [FORCE] Killing PID $pid on port $port"
            kill_pid "$pid"
        done
    fi
}

# ── Sweep any leftover python.exe processes that are running benchmark
# scripts (catches sub-server ports we don't track in PORTS, e.g. the
# phishing-side ports 5511/5513/5515/... bound by run_servers.py). ────
sweep_orphans() {
    if ! is_windows; then
        # Linux/macOS: pattern-match python processes whose command-line
        # references the benchmark trees. Catches sub-server children
        # spawned by run_servers.py whose ports aren't in PORTS (e.g.
        # job_portal's port 12999, e7_ninite's 5511, etc.) and orphan
        # children whose parents were already killed by Strategy 1/2.
        #
        # Excludes known dev tooling (jupyter, pytest, language-server,
        # ipykernel, etc.) so a running notebook doesn't get reaped.
        if command -v pkill >/dev/null 2>&1; then
            # Two-pass: print what would die, then kill it. Quiet on no-match.
            local matched
            matched=$(pgrep -af 'python.*all_websites|python.*run_servers\.py|python.*phishing_|python.*mailbox' 2>/dev/null \
                      | grep -viE 'jupyter|jedi|pytest|language-server|ipykernel|debugpy|pylance')
            if [ -n "$matched" ]; then
                echo "  [SWEEP] Killing $(echo "$matched" | wc -l) benchmark python process(es):"
                echo "$matched" | sed 's/^/    /'
                # SIGTERM, then SIGKILL after a beat.
                pkill -f 'python.*all_websites|python.*run_servers\.py|python.*phishing_|python.*mailbox' 2>/dev/null
                sleep 1
                pkill -9 -f 'python.*all_websites|python.*run_servers\.py|python.*phishing_|python.*mailbox' 2>/dev/null
            else
                echo "  [SWEEP] No leftover benchmark python processes found"
            fi
        else
            echo "  [SWEEP] pkill not available; skipping orphan sweep"
        fi
        return 0
    fi
    powershell.exe -NoProfile -Command "
        \$procs = @(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" -ErrorAction SilentlyContinue | Where-Object {
            \$cmd = \$_.CommandLine
            \$exe = \$_.ExecutablePath
            if (-not \$cmd) { return \$false }
            # Exclude known non-benchmark dev tools that share the project venv
            if (\$cmd -match '(jedi|jupyter|notebook|pylance|language-server|pytest|ms-python|debugpy|ipykernel)') { return \$false }
            # Match the benchmark script names (handles truncated subprocess children
            # like 'python.exe app.py' that don't show all_websites in their cmdline)
            if (\$cmd -like '*all_websites*' -or
                \$cmd -like '*run_servers.py*' -or
                \$cmd -like '* app.py*' -or
                \$cmd -like '* server.py*' -or
                \$cmd -like '*\app.py*' -or
                \$cmd -like '*\server.py*' -or
                \$cmd -like '*/app.py*' -or
                \$cmd -like '*/server.py*' -or
                \$cmd -like '*phishing_*' -or
                \$cmd -like '*mailbox*') {
                return \$true
            }
            # Last resort: python.exe from the project's .venv that's not a known
            # dev tool (caught by the exclusion list above). Safe-ish because the
            # exclusion list covers VSCode/Jupyter/etc.
            if (\$exe -and \$exe -like '*llmsocialengg*\.venv*python.exe') { return \$true }
            return \$false
        })
        Write-Host (\"  [SWEEP] Found \" + \$procs.Count + ' benchmark python.exe process(es)')
        foreach (\$p in \$procs) {
            Write-Host (\"  [SWEEP] Killing PID \" + \$p.ProcessId)
            Stop-Process -Id \$p.ProcessId -Force -ErrorAction SilentlyContinue
        }
    "
}

# ── Port check (Windows via PowerShell TcpClient; Linux/macOS via bash /dev/tcp) ──
port_up() {
    local port="$1"
    if is_windows; then
        powershell.exe -NoProfile -Command "
            try {
                \$tcp = New-Object System.Net.Sockets.TcpClient
                \$tcp.Connect('127.0.0.1', $port)
                \$tcp.Close()
                exit 0
            } catch { exit 1 }
        " 2>/dev/null
        return $?
    else
        # Native bash TCP port check for Linux/macOS — avoids dependency on
        # nc / lsof which aren't installed by default on every distro.
        (echo > /dev/tcp/127.0.0.1/$port) >/dev/null 2>&1
        return $?
    fi
}

# ── Stop all servers ──────────────────────────────────────────────────
stop_servers() {
    echo ""
    echo "  Stopping all benchmark servers..."

    # Strategy 1: best-effort kill of every PID we recorded at spawn.
    # On Git Bash these are msys2 PIDs and often won't kill python.exe,
    # but on Unix they do — keep for portability.
    if [ -f "$PIDFILE" ]; then
        while read -r pid; do
            [ -z "$pid" ] && continue
            kill_pid "$pid"
        done < "$PIDFILE"
        rm -f "$PIDFILE"
    fi

    # Strategy 2: kill whatever is listening on every known benchmark
    # port via OS-level port -> PID resolution (taskkill on Windows).
    for port in "${PORTS[@]}"; do
        kill_port "$port"
    done

    # Strategy 3: Windows-only nuclear sweep — find any python.exe
    # whose command line references all_websites/ and kill it. Catches
    # sub-server ports the multi-server run_servers.py bind that are
    # not in the PORTS array, plus any orphaned children.
    sweep_orphans

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
    # nohup makes the child immune to SIGHUP, so it survives this bash script
    # exiting. Without it, non-debug Flask single-process servers die because
    # MSYS2/Git Bash propagates a hangup signal to background jobs on exit.
    nohup $actual_cmd > "$logfile" 2>&1 &
    pid=$!
    disown "$pid" 2>/dev/null || true
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
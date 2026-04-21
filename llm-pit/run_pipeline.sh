#!/bin/bash
# ============================================================================
# LLM Website Generation Pipeline
# ============================================================================
# Spins up Claude Code (Sonnet) to generate and review benchmark websites
# for the Social Engineering Attack Benchmark.
#
# Usage:
#   ./run_pipeline.sh                    # Run all pending websites
#   ./run_pipeline.sh --list             # Show status of all websites
#   ./run_pipeline.sh --only key1,key2   # Run only specific websites
#   ./run_pipeline.sh --reset key1       # Reset a website to re-run it
#   ./run_pipeline.sh --reset-all        # Reset all websites
#   ./run_pipeline.sh --dry-run          # Show what would be done
#
# Checkpointing:
#   Each website tracks its state in <output_dir>/<website>/.pipeline_state
#   States: pending → generating → generated → reflecting → completed
#   If interrupted, re-running the script resumes from the last state.
#
# Adding new websites:
#   1. Add entries to website_prompts.sh
#   2. Re-run this script — it skips completed ones automatically.
# ============================================================================

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPTS_FILE="${SCRIPT_DIR}/website_prompts.sh"
OUTPUT_DIR="${SCRIPT_DIR}/websites"         # Root output directory
LOG_DIR="${SCRIPT_DIR}/logs"                # Pipeline logs
MODEL="sonnet"                             # Claude Code model
EFFORT="high"                              # Claude Code effort level

# Claude Code env vars
export CLAUDE_CODE_DISABLE_1M_CONTEXT=1

# ── Color codes ────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No color

# ── Helper functions ───────────────────────────────────────────────────────

log_info()    { echo -e "${BLUE}[INFO]${NC}  $(date '+%H:%M:%S') $*"; }
log_success() { echo -e "${GREEN}[DONE]${NC}  $(date '+%H:%M:%S') $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $(date '+%H:%M:%S') $*"; }
log_error()   { echo -e "${RED}[FAIL]${NC}  $(date '+%H:%M:%S') $*"; }
log_step()    { echo -e "${CYAN}[STEP]${NC}  $(date '+%H:%M:%S') $*"; }

# Get the pipeline state for a website
get_state() {
    local dir="$1"
    local state_file="${OUTPUT_DIR}/${dir}/.pipeline_state"
    if [[ -f "$state_file" ]]; then
        cat "$state_file"
    else
        echo "pending"
    fi
}

# Set the pipeline state for a website
set_state() {
    local dir="$1"
    local state="$2"
    mkdir -p "${OUTPUT_DIR}/${dir}"
    echo "$state" > "${OUTPUT_DIR}/${dir}/.pipeline_state"
}

# Parse a website entry (pipe-delimited)
parse_entry() {
    local entry="$1"
    IFS='|' read -r W_KEY W_DIR W_GEN_PROMPT W_REFLECT_PROMPT <<< "$entry"
}

# Run a Claude Code pass
run_claude() {
    local work_dir="$1"
    local prompt="$2"
    local log_file="$3"
    local pass_name="$4"

    log_step "Running ${pass_name} pass in ${work_dir}..."

    # Ensure work directory exists
    mkdir -p "$work_dir"

    # Run Claude Code in non-interactive mode
    if claude \
        --model "$MODEL" \
        --effort "$EFFORT" \
        --dangerously-skip-permissions \
        -p "$prompt" \
        --output-format text \
        2>&1 | tee "$log_file"; then
        return 0
    else
        local exit_code=$?
        log_error "Claude Code exited with code ${exit_code} during ${pass_name}"
        return $exit_code
    fi
}

# Print a status summary table
print_status() {
    echo ""
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  Website Generation Pipeline — Status${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    printf "  ${BOLD}%-25s %-15s %-10s${NC}\n" "SCAFFOLD KEY" "DIRECTORY" "STATE"
    echo "  ─────────────────────────────────────────────────────────────"

    local total=0 completed=0 pending=0 in_progress=0

    for entry in "${WEBSITES[@]}"; do
        parse_entry "$entry"
        local state
        state=$(get_state "$W_DIR")
        total=$((total + 1))

        local color="$NC"
        case "$state" in
            completed)    color="$GREEN"; completed=$((completed + 1)) ;;
            pending)      color="$YELLOW"; pending=$((pending + 1)) ;;
            *)            color="$CYAN"; in_progress=$((in_progress + 1)) ;;
        esac

        printf "  %-25s %-15s ${color}%-10s${NC}\n" "$W_KEY" "$W_DIR" "$state"
    done

    echo "  ─────────────────────────────────────────────────────────────"
    echo -e "  Total: ${total}  ${GREEN}Completed: ${completed}${NC}  ${CYAN}In Progress: ${in_progress}${NC}  ${YELLOW}Pending: ${pending}${NC}"
    echo ""
}

# ── Load prompts config ───────────────────────────────────────────────────
if [[ ! -f "$PROMPTS_FILE" ]]; then
    log_error "Prompts file not found: $PROMPTS_FILE"
    exit 1
fi
source "$PROMPTS_FILE"

# ── Parse CLI arguments ───────────────────────────────────────────────────
ACTION="run"
ONLY_KEYS=""
RESET_KEY=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --list)
            ACTION="list"
            shift ;;
        --only)
            ONLY_KEYS="$2"
            shift 2 ;;
        --reset)
            ACTION="reset"
            RESET_KEY="$2"
            shift 2 ;;
        --reset-all)
            ACTION="reset-all"
            shift ;;
        --dry-run)
            DRY_RUN=true
            shift ;;
        --help|-h)
            echo "Usage: $0 [--list] [--only key1,key2] [--reset key] [--reset-all] [--dry-run]"
            exit 0 ;;
        *)
            log_error "Unknown argument: $1"
            exit 1 ;;
    esac
done

# ── Handle actions ────────────────────────────────────────────────────────

if [[ "$ACTION" == "list" ]]; then
    print_status
    exit 0
fi

if [[ "$ACTION" == "reset-all" ]]; then
    for entry in "${WEBSITES[@]}"; do
        parse_entry "$entry"
        set_state "$W_DIR" "pending"
        log_info "Reset ${W_KEY} → pending"
    done
    log_success "All websites reset."
    exit 0
fi

if [[ "$ACTION" == "reset" ]]; then
    found=false
    for entry in "${WEBSITES[@]}"; do
        parse_entry "$entry"
        if [[ "$W_KEY" == "$RESET_KEY" ]]; then
            set_state "$W_DIR" "pending"
            log_success "Reset ${W_KEY} → pending"
            found=true
            break
        fi
    done
    if [[ "$found" == false ]]; then
        log_error "Unknown scaffold key: $RESET_KEY"
        exit 1
    fi
    exit 0
fi

# ── Main pipeline ─────────────────────────────────────────────────────────

mkdir -p "$OUTPUT_DIR" "$LOG_DIR"

# Build filter set if --only was provided
declare -A ONLY_SET
if [[ -n "$ONLY_KEYS" ]]; then
    IFS=',' read -ra keys <<< "$ONLY_KEYS"
    for k in "${keys[@]}"; do
        ONLY_SET["$k"]=1
    done
fi

# Timestamp for this run
RUN_TS=$(date '+%Y%m%d_%H%M%S')
RUN_LOG="${LOG_DIR}/run_${RUN_TS}.log"

echo ""
echo -e "${BOLD}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║      Social Engineering Benchmark — Website Generator        ║${NC}"
echo -e "${BOLD}║      Model: ${MODEL}  |  Effort: ${EFFORT}                          ║${NC}"
echo -e "${BOLD}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

total=${#WEBSITES[@]}
completed_before=0
processed=0
failed=0

# Count already completed
for entry in "${WEBSITES[@]}"; do
    parse_entry "$entry"
    state=$(get_state "$W_DIR")
    [[ "$state" == "completed" ]] && completed_before=$((completed_before + 1))
done

log_info "Found ${total} websites, ${completed_before} already completed."

for i in "${!WEBSITES[@]}"; do
    entry="${WEBSITES[$i]}"
    parse_entry "$entry"
    idx=$((i + 1))

    # Skip if --only filter is active and this key isn't in the set
    if [[ -n "$ONLY_KEYS" ]] && [[ -z "${ONLY_SET[$W_KEY]:-}" ]]; then
        continue
    fi

    state=$(get_state "$W_DIR")
    work_dir="${OUTPUT_DIR}/${W_DIR}"
    gen_log="${LOG_DIR}/${W_KEY}_generate_${RUN_TS}.log"
    ref_log="${LOG_DIR}/${W_KEY}_reflect_${RUN_TS}.log"

    echo ""
    echo -e "${BOLD}───────────────────────────────────────────────────────────────${NC}"
    echo -e "${BOLD}  [${idx}/${total}] ${W_KEY}${NC}  (directory: ${W_DIR})"
    echo -e "${BOLD}───────────────────────────────────────────────────────────────${NC}"

    # ── Skip if completed ──
    if [[ "$state" == "completed" ]]; then
        log_success "Already completed — skipping."
        continue
    fi

    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY RUN] Would process ${W_KEY} (current state: ${state})"
        continue
    fi

    # ── PASS 1: Generate ──
    if [[ "$state" == "pending" || "$state" == "generating" ]]; then
        set_state "$W_DIR" "generating"

        full_gen_prompt="${SHARED_CONTEXT}

${W_GEN_PROMPT}

IMPORTANT: Create all files inside the current working directory. The website directory is: $(pwd)/${work_dir}
Create the complete Flask application with all templates, static files, and config.json.
Ensure the app can be started with 'python app.py' or 'python run_servers.py'."

        if run_claude "$work_dir" "$full_gen_prompt" "$gen_log" "generate"; then
            set_state "$W_DIR" "generated"
            log_success "Generation pass completed for ${W_KEY}"
        else
            set_state "$W_DIR" "generating"  # Keep in generating state for retry
            log_error "Generation failed for ${W_KEY} — will retry on next run"
            failed=$((failed + 1))
            continue
        fi
    fi

    # ── PASS 2: Reflect & Fix ──
    if [[ "$state" == "generated" || "$state" == "reflecting" ]]; then
        set_state "$W_DIR" "reflecting"

        full_ref_prompt="${W_REFLECT_PROMPT}

The website files are in the current working directory: $(pwd)/${work_dir}
Review all files, test for issues, and fix anything that is broken or missing.
Do NOT delete or remove any existing features — only fix and improve."

        if run_claude "$work_dir" "$full_ref_prompt" "$ref_log" "reflect"; then
            set_state "$W_DIR" "completed"
            log_success "Reflection pass completed for ${W_KEY}"
        else
            set_state "$W_DIR" "reflecting"  # Keep in reflecting state for retry
            log_error "Reflection failed for ${W_KEY} — will retry on next run"
            failed=$((failed + 1))
            continue
        fi
    fi

    processed=$((processed + 1))
    log_success "${W_KEY} fully completed! (${processed} processed this run)"

done

# ── Final Summary ─────────────────────────────────────────────────────────

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  Pipeline Run Complete${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
echo -e "  Processed this run:  ${GREEN}${processed}${NC}"
echo -e "  Failed this run:     ${RED}${failed}${NC}"
echo -e "  Previously done:     ${completed_before}"
echo -e "  Total websites:      ${total}"
echo -e "  Run log:             ${RUN_LOG}"
echo ""

print_status

if [[ $failed -gt 0 ]]; then
    log_warn "Some websites failed. Re-run the script to retry them."
    exit 1
fi
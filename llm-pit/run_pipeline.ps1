# ============================================================================
# LLM Website Generation Pipeline (PowerShell)
# ============================================================================
# Spins up Claude Code (Sonnet) to generate and review benchmark websites
# for the Social Engineering Attack Benchmark.
#
# Usage:
#   .\run_pipeline.ps1                        # Run all pending websites
#   .\run_pipeline.ps1 -List                  # Show status of all websites
#   .\run_pipeline.ps1 -Only "key1,key2"      # Run only specific websites
#   .\run_pipeline.ps1 -Reset "key1"          # Reset a website to re-run it
#   .\run_pipeline.ps1 -ResetAll              # Reset all websites
#   .\run_pipeline.ps1 -DryRun                # Show what would be done
#
# Checkpointing:
#   Each website tracks its state in <output_dir>/<website>/.pipeline_state
#   States: pending -> generating -> generated -> reflecting -> completed
#   If interrupted, re-running the script resumes from the last state.
#
# Adding new websites:
#   1. Add entries to website_prompts.ps1
#   2. Re-run this script — it skips completed ones automatically.
# ============================================================================

param(
    [switch]$List,
    [string]$Only = "",
    [string]$Reset = "",
    [switch]$ResetAll,
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"

# ── Configuration ──────────────────────────────────────────────────────────
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PromptsFile = Join-Path $ScriptDir "website_prompts.ps1"
$OutputDir  = Join-Path $ScriptDir "websites"
$LogDir     = Join-Path $ScriptDir "logs"
$Model      = "sonnet"
$Effort     = "high"

# Claude Code env var
$env:CLAUDE_CODE_DISABLE_1M_CONTEXT = "1"

# ── Load prompts config ───────────────────────────────────────────────────
if (-not (Test-Path $PromptsFile)) {
    Write-Host "[FAIL] Prompts file not found: $PromptsFile" -ForegroundColor Red
    exit 1
}
. $PromptsFile

# ── Helper functions ───────────────────────────────────────────────────────

function Log-Info    { param($Msg) Write-Host "[INFO]  $(Get-Date -Format 'HH:mm:ss') $Msg" -ForegroundColor Blue }
function Log-Success { param($Msg) Write-Host "[DONE]  $(Get-Date -Format 'HH:mm:ss') $Msg" -ForegroundColor Green }
function Log-Warn    { param($Msg) Write-Host "[WARN]  $(Get-Date -Format 'HH:mm:ss') $Msg" -ForegroundColor Yellow }
function Log-Error   { param($Msg) Write-Host "[FAIL]  $(Get-Date -Format 'HH:mm:ss') $Msg" -ForegroundColor Red }
function Log-Step    { param($Msg) Write-Host "[STEP]  $(Get-Date -Format 'HH:mm:ss') $Msg" -ForegroundColor Cyan }

function Get-PipelineState {
    param([string]$Dir)
    $stateFile = Join-Path (Join-Path $OutputDir $Dir) ".pipeline_state"
    if (Test-Path $stateFile) {
        return (Get-Content $stateFile -Raw).Trim()
    }
    return "pending"
}

function Set-PipelineState {
    param([string]$Dir, [string]$State)
    $targetDir = Join-Path $OutputDir $Dir
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
    $State | Out-File -FilePath (Join-Path $targetDir ".pipeline_state") -NoNewline -Encoding utf8
}

function Run-ClaudeCode {
    param(
        [string]$WorkDir,
        [string]$Prompt,
        [string]$LogFile,
        [string]$PassName
    )

    Log-Step "Running $PassName pass in $WorkDir..."

    if (-not (Test-Path $WorkDir)) {
        New-Item -ItemType Directory -Path $WorkDir -Force | Out-Null
    }

    # Write prompt to a temp file to avoid command-line length/escaping issues
    $promptFile = Join-Path $env:TEMP "claude_prompt_$(Get-Random).txt"
    $Prompt | Out-File -FilePath $promptFile -Encoding utf8

    try {
        Push-Location $WorkDir

        # Pipe the prompt file into claude via cmd /c
        # This avoids Start-Process argument mangling entirely
        cmd /c "type `"$promptFile`" | claude --model $Model --effort $Effort --dangerously-skip-permissions -p - --output-format text > `"$LogFile`" 2>&1"
        $exitCode = $LASTEXITCODE

        Pop-Location

        if ($exitCode -eq 0) {
            return $true
        } else {
            Log-Error "Claude Code exited with code $exitCode during $PassName"
            return $false
        }
    }
    catch {
        Pop-Location -ErrorAction SilentlyContinue
        Log-Error "Exception during ${PassName}: $_"
        return $false
    }
    finally {
        if (Test-Path $promptFile) { Remove-Item $promptFile -Force }
    }
}

function Print-Status {
    Write-Host ""
    Write-Host "==================================================================" -ForegroundColor White
    Write-Host "  Website Generation Pipeline - Status" -ForegroundColor White
    Write-Host "==================================================================" -ForegroundColor White
    Write-Host ("  {0,-25} {1,-22} {2,-12}" -f "SCAFFOLD KEY", "DIRECTORY", "STATE") -ForegroundColor White
    Write-Host "  ------------------------------------------------------------------"

    $total = 0; $completed = 0; $pending = 0; $inProgress = 0

    foreach ($w in $WEBSITES) {
        $state = Get-PipelineState -Dir $w.Directory
        $total++

        $color = "White"
        switch ($state) {
            "completed"  { $color = "Green";  $completed++ }
            "pending"    { $color = "Yellow"; $pending++ }
            default      { $color = "Cyan";   $inProgress++ }
        }

        Write-Host ("  {0,-25} {1,-22} " -f $w.Key, $w.Directory) -NoNewline
        Write-Host ("{0,-12}" -f $state) -ForegroundColor $color
    }

    Write-Host "  ------------------------------------------------------------------"
    Write-Host -NoNewline "  Total: $total  "
    Write-Host -NoNewline "Completed: $completed  " -ForegroundColor Green
    Write-Host -NoNewline "In Progress: $inProgress  " -ForegroundColor Cyan
    Write-Host "Pending: $pending" -ForegroundColor Yellow
    Write-Host ""
}

# ── Handle actions ────────────────────────────────────────────────────────

if ($List) {
    Print-Status
    exit 0
}

if ($ResetAll) {
    foreach ($w in $WEBSITES) {
        Set-PipelineState -Dir $w.Directory -State "pending"
        Log-Info "Reset $($w.Key) -> pending"
    }
    Log-Success "All websites reset."
    exit 0
}

if ($Reset -ne "") {
    $found = $false
    foreach ($w in $WEBSITES) {
        if ($w.Key -eq $Reset) {
            Set-PipelineState -Dir $w.Directory -State "pending"
            Log-Success "Reset $($w.Key) -> pending"
            $found = $true
            break
        }
    }
    if (-not $found) {
        Log-Error "Unknown scaffold key: $Reset"
        exit 1
    }
    exit 0
}

# ── Main pipeline ─────────────────────────────────────────────────────────

if (-not (Test-Path $OutputDir)) { New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null }
if (-not (Test-Path $LogDir))    { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }

# Build filter set if -Only was provided
$onlySet = @{}
if ($Only -ne "") {
    $Only.Split(",") | ForEach-Object { $onlySet[$_.Trim()] = $true }
}

# Timestamp for this run
$runTs  = Get-Date -Format "yyyyMMdd_HHmmss"
$runLog = Join-Path $LogDir "run_$runTs.log"

Write-Host ""
Write-Host "==================================================================" -ForegroundColor White
Write-Host "  Social Engineering Benchmark - Website Generator" -ForegroundColor White
Write-Host "  Model: $Model  |  Effort: $Effort" -ForegroundColor White
Write-Host "==================================================================" -ForegroundColor White
Write-Host ""

$total = $WEBSITES.Count
$completedBefore = 0
$processed = 0
$failed = 0

# Count already completed
foreach ($w in $WEBSITES) {
    $state = Get-PipelineState -Dir $w.Directory
    if ($state -eq "completed") { $completedBefore++ }
}

Log-Info "Found $total websites, $completedBefore already completed."

for ($i = 0; $i -lt $WEBSITES.Count; $i++) {
    $w   = $WEBSITES[$i]
    $idx = $i + 1

    # Skip if -Only filter is active and this key isn't in the set
    if ($onlySet.Count -gt 0 -and -not $onlySet.ContainsKey($w.Key)) {
        continue
    }

    $state   = Get-PipelineState -Dir $w.Directory
    $workDir = Join-Path $OutputDir $w.Directory
    $genLog  = Join-Path $LogDir "$($w.Key)_generate_$runTs.log"
    $refLog  = Join-Path $LogDir "$($w.Key)_reflect_$runTs.log"

    Write-Host ""
    Write-Host "-------------------------------------------------------------------" -ForegroundColor White
    Write-Host "  [$idx/$total] $($w.Key)  (directory: $($w.Directory))" -ForegroundColor White
    Write-Host "-------------------------------------------------------------------" -ForegroundColor White

    # ── Skip if completed ──
    if ($state -eq "completed") {
        Log-Success "Already completed - skipping."
        continue
    }

    if ($DryRun) {
        Log-Info "[DRY RUN] Would process $($w.Key) (current state: $state)"
        continue
    }

    # ── PASS 1: Generate ──
    if ($state -eq "pending" -or $state -eq "generating") {
        Set-PipelineState -Dir $w.Directory -State "generating"

        $fullGenPrompt = @"
$SHARED_CONTEXT

$($w.GenPrompt)

IMPORTANT: Create all files inside the current working directory.
Create the complete Flask application with all templates, static files, and config.json.
Ensure the app can be started with 'python app.py' or 'python run_servers.py'.
"@

        $result = Run-ClaudeCode -WorkDir $workDir -Prompt $fullGenPrompt -LogFile $genLog -PassName "generate"

        if ($result) {
            Set-PipelineState -Dir $w.Directory -State "generated"
            Log-Success "Generation pass completed for $($w.Key)"
        } else {
            Set-PipelineState -Dir $w.Directory -State "generating"
            Log-Error "Generation failed for $($w.Key) - will retry on next run"
            $failed++
            continue
        }
    }

    # ── PASS 2: Reflect & Fix ──
    if ($state -eq "generated" -or $state -eq "reflecting") {
        Set-PipelineState -Dir $w.Directory -State "reflecting"

        $fullRefPrompt = @"
$($w.RefPrompt) $REFLECT_SUFFIX

The website files are in the current working directory.
Review all files, test for issues, and fix anything that is broken or missing.
Do NOT delete or remove any existing features - only fix and improve.
"@

        $result = Run-ClaudeCode -WorkDir $workDir -Prompt $fullRefPrompt -LogFile $refLog -PassName "reflect"

        if ($result) {
            Set-PipelineState -Dir $w.Directory -State "completed"
            Log-Success "Reflection pass completed for $($w.Key)"
        } else {
            Set-PipelineState -Dir $w.Directory -State "reflecting"
            Log-Error "Reflection failed for $($w.Key) - will retry on next run"
            $failed++
            continue
        }
    }

    $processed++
    Log-Success "$($w.Key) fully completed! ($processed processed this run)"
}

# ── Final Summary ─────────────────────────────────────────────────────────

Write-Host ""
Write-Host "==================================================================" -ForegroundColor White
Write-Host "  Pipeline Run Complete" -ForegroundColor White
Write-Host "==================================================================" -ForegroundColor White
Write-Host -NoNewline "  Processed this run:  "; Write-Host "$processed" -ForegroundColor Green
Write-Host -NoNewline "  Failed this run:     "; Write-Host "$failed" -ForegroundColor Red
Write-Host "  Previously done:     $completedBefore"
Write-Host "  Total websites:      $total"
Write-Host "  Run log:             $runLog"
Write-Host ""

Print-Status

if ($failed -gt 0) {
    Log-Warn "Some websites failed. Re-run the script to retry them."
    exit 1
}
"""
Quick DR judge runner for 200 samples.
Usage: 
    $env:GROQ_API_KEY="your_key"
    uv run python _run_dr_judge.py
"""
import json
import asyncio
import os
from pathlib import Path
import sys
sys.path.insert(0, '.')

from agent.evaluation.dr_judge import DRJudge

# Load the 200 samples
with open('agent/logs/dr_labeling_samples.json') as f:
    samples = json.load(f)

print(f"Loaded {len(samples)} samples")

# Extract file paths
log_files = [Path(s['file']) for s in samples if Path(s['file']).exists()]
print(f"Found {len(log_files)} existing log files")

# Run DR judge on these
async def main():
    api_key = (
        os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("API_KEY")
    )
    if not api_key:
        print("ERROR: Set OPENROUTER_API_KEY environment variable")
        return

    judge = DRJudge(
        primary_model="meta-llama/llama-4-scout",
        secondary_model=None,
        groq_api_key=api_key,  # kwarg name is legacy; value is just the api key
    )
    results = await judge.judge_session_batch(log_files, run_secondary=False)
    
    # Save results
    output = {
        "primary_judge": "meta-llama/llama-4-scout",
        "num_sessions": len(results),
        "sessions": results
    }
    
    with open('agent/logs/dr_labeling_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    # Print summary
    detected = sum(1 for r in results if r.get('any_detection'))
    print(f"\nResults: {detected}/{len(results)} sessions had at least one detection")
    print(f"DR: {detected/len(results)*100:.1f}%")
    print(f"Saved to: agent/logs/dr_labeling_results.json")

asyncio.run(main())
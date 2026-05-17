"""Move C0 orphan session.json files (those without a paired .score.json)
into Llama_4_Scout_17B_(Groq)/C0/_aborted/ . Idempotent."""
import shutil
from pathlib import Path

C0 = Path(__file__).parent / "Llama_4_Scout_17B_(Groq)" / "C0"
ABORTED = C0 / "_aborted"
ABORTED.mkdir(exist_ok=True)

scored_stems = set()
for p in C0.glob("*.score.json"):
    # session_file.score.json -> session_file
    stem = p.name.removesuffix(".score.json")
    scored_stems.add(stem)

moved = []
for p in C0.glob("*.json"):
    if p.name.endswith(".score.json"):
        continue
    stem = p.name.removesuffix(".json")
    if stem in scored_stems:
        continue  # paired survivor
    # orphan
    dest = ABORTED / p.name
    shutil.move(str(p), str(dest))
    moved.append(p.name)

print(f"moved {len(moved)} orphan session.json files to {ABORTED.relative_to(Path(__file__).parent)}/")
if moved[:5]:
    print(f"  sample: {moved[:5]}")
remaining = list(C0.glob("*.json"))
print(f"C0/ now contains {len(remaining)} files at top level (excluding _aborted/)")

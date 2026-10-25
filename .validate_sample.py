import csv
from pathlib import Path

root = Path(r"d:\Professional work\GIT\hackerrank-orchestrate-october26-main\hackerrank-orchestrate-october26-main")
our = list(csv.DictReader(open(root / "output.csv", newline="", encoding="utf-8")))
sample = list(csv.DictReader(open(root / "dataset" / "sample_output.csv", newline="", encoding="utf-8")))
print("generated", len(our), "sample", len(sample))
mismatch = []
by_id = {r["case_id"]: r for r in our}
for row in sample:
    ours = by_id.get(row["case_id"])
    if ours is None:
        mismatch.append(("missing", row["case_id"]))
        continue
    if ours["deletion_status"] != row["deletion_status"] or ours["steps_json"] != row["steps_json"]:
        mismatch.append((row["case_id"], ours, row))
print("mismatches", len(mismatch))
for x in mismatch[:5]:
    print(x)

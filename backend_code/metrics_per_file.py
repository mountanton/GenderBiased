import json
from pathlib import Path

BASE_DIR = Path("output")

file_results = []

def normalize_answer(ans):
    """
    Normalize answers like:
    'Yes', 'Yes.', '# Answer: Yes', etc.
    """
    if not isinstance(ans, str):
        return None

    ans = ans.strip().lower()

    if "yes" in ans:
        return "Yes"

    if "no" in ans:
        return "No"
    return "No"


# =========================
# PROCESS EACH FILE
# =========================

for file_path in BASE_DIR.glob("*.json"):

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    yes_count = 0
    no_count = 0

    for topic_block in data["results"]:

        for item in topic_block["results"]:

            for vr in item.get("validation_results", []):

                ans = normalize_answer(vr.get("answer"))

                if ans == "Yes":
                    yes_count += 1

                elif ans == "No":
                    no_count += 1

    total = yes_count + no_count

    yes_pct = (yes_count / total) * 100 if total > 0 else 0
    no_pct = (no_count / total) * 100 if total > 0 else 0

    model_name =file_path

    file_results.append({
        "model": model_name,
        "yes": yes_count,
        "no": no_count,
        "yes_pct": yes_pct,
        "no_pct": no_pct
    })


# =========================
# PRINT PER FILE
# =========================

print("\n===== PER FILE =====")

for r in file_results:

    print(f"\nMODEL: {r['model']}")
    print(f"  Yes: {r['yes']} ({r['yes_pct']:.2f}%)")
    print(f"  No : {r['no']} ({r['no_pct']:.2f}%)")


# =========================
# AVERAGE ACROSS FILES
# =========================

avg_yes_pct = sum(r["yes_pct"] for r in file_results) / len(file_results)
avg_no_pct = sum(r["no_pct"] for r in file_results) / len(file_results)

avg_yes = sum(r["yes"] for r in file_results) / len(file_results)
avg_no = sum(r["no"] for r in file_results) / len(file_results)

print("\n===== AVERAGE ACROSS FILES =====")
print(f"Average Yes count : {avg_yes:.2f}")
print(f"Average No count  : {avg_no:.2f}")
print(f"Average Yes %     : {avg_yes_pct:.2f}%")
print(f"Average No %      : {avg_no_pct:.2f}%")
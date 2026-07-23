import json
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path("output")

overall = {"Yes": 0, "No": 0}
per_topic = defaultdict(lambda: {"Yes": 0, "No": 0})

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


for file_path in BASE_DIR.glob("*.json"):

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for topic_block in data["results"]:

        # USE TOPIC NAME INSTEAD OF TOPIC ID
        topic_name = topic_block["topic"]

        for item in topic_block["results"]:

            for vr in item.get("validation_results", []):

                ans = normalize_answer(vr.get("answer"))

                if ans in ["Yes", "No"]:
                    overall[ans] += 1
                    per_topic[topic_name][ans] += 1


# =========================
# OVERALL STATS
# =========================

total = overall["Yes"] + overall["No"]

print("\n===== OVERALL =====")
print(f"Yes: {overall['Yes']}")
print(f"No : {overall['No']}")

if total > 0:
    print(f"Yes %: {100 * overall['Yes'] / total:.2f}%")
    print(f"No  %: {100 * overall['No'] / total:.2f}%")


# =========================
# PER TOPIC STATS
# =========================

print("\n===== PER TOPIC =====")

for topic_name, stats in per_topic.items():

    total_topic = stats["Yes"] + stats["No"]

    yes_pct = (
        100 * stats["Yes"] / total_topic
        if total_topic > 0 else 0
    )

    no_pct = (
        100 * stats["No"] / total_topic
        if total_topic > 0 else 0
    )

    print(f"\nTOPIC: {topic_name}")
    print(f"  Yes: {stats['Yes']} ({yes_pct:.2f}%)")
    print(f"  No : {stats['No']} ({no_pct:.2f}%)")
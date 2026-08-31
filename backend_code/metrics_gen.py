import json
import yaml
from pathlib import Path
from collections import defaultdict


with open('conf.yaml', 'r', encoding = 'utf-8') as f:
    config = yaml.safe_load(f)

BASE_DIR = Path(config['file_path_output'])

all_stats = {}

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
# process every subfolder 
# =========================
for model_folder in BASE_DIR.iterdir():

    # Only look at directories
    if not model_folder.is_dir():
        continue

    overall = {"Yes": 0, "No": 0}
    per_topic = defaultdict(lambda: {"Yes": 0, "No": 0})

    file_results = []

    res_files = list(model_folder.glob("results_*.json"))

    for file_path in res_files:

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


        file_results.append({
            "model": file_path.name,
            "yes": yes_count,
            "no": no_count,
            "yes_pct": yes_pct,
            "no_pct": no_pct
        })


    # =========================
    # AVERAGE ACROSS FILES
    # =========================

    avg_yes_pct = sum(r["yes_pct"] for r in file_results) / len(file_results)
    avg_no_pct = sum(r["no_pct"] for r in file_results) / len(file_results)

    avg_yes = sum(r["yes"] for r in file_results) / len(file_results)
    avg_no = sum(r["no"] for r in file_results) / len(file_results)

    # Added min and max yes percentage
    min_yes_pct = min(r["yes_pct"] for r in file_results)
    max_yes_pct = max(r["yes_pct"] for r in file_results)
    

    for file_path in res_files:

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
    overall["yes_pct"] = (100 * overall["Yes"] / total) if total > 0 else 0
    overall["no_pct"] = (100 * overall["No"] / total) if total > 0 else 0

    # =========================
    # PER TOPIC STATS
    # =========================

    topic_dict = {}
    for topic_name, stats in per_topic.items():
        total_topics = stats["Yes"] + stats["No"]
        topic_dict[topic_name] = {
            "Yes": stats["Yes"],
            "No": stats["No"],
            "yes_pct": (100 * stats["Yes"] / total_topics) if total_topics > 0 else 0,
            "no_pct": (100 * stats["No"] / total_topics) if total_topics > 0 else 0
        }



    all_stats[model_folder.name] = {
        "overall": overall,
        "metrics_per_topic": topic_dict,
        "model_averages": {
            "avg_yes": avg_yes,
            "avg_no": avg_no,
            "avg_yes_pct": avg_yes_pct,
            "avg_no_pct": avg_no_pct,
            "min_yes_pct": min_yes_pct,
            "max_yes_pct": max_yes_pct,

            # Statistics for every individual run
            "runs": file_results
        }
    }


with open("all_stats.json", "w", encoding="utf-8") as f:
    json.dump(all_stats, f, indent=4, ensure_ascii=False)

print("All metrics calculated")    

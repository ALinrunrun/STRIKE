# Modify the `target_file` then Run 
# python summarize_eval_res.py

# OUTPUT:
# answer.json
# Method         avg_naturalness      avg_semantic     avg_all
# alert                     x.xx              x.xx        x.xx
# beam                      x.xx              x.xx        x.xx
# coda                      x.xx              x.xx        x.xx
# itgen                     x.xx              x.xx        x.xx
# strike                    x.xx              x.xx        x.xx

import json
from collections import defaultdict

target_file = "jintao2_results.json"

with open(target_file, "r", encoding="utf-8") as f:
    data = json.load(f)

stats = defaultdict(lambda: {"naturalness": [], "semantic": []})

# Group and summarize by "Method"
for item in data:
    method = item["Method"]
    stats[method]["naturalness"].append(item["naturalness"])
    stats[method]["semantic"].append(item["semantic"])

print(target_file)
print(f"{'Method':<12}{'avg_naturalness':>18}{'avg_semantic':>18}{'avg_all':>12}")
print("-" * 60)

for method, vals in sorted(stats.items()):
    avg_nat = sum(vals["naturalness"]) / len(vals["naturalness"])
    avg_sem = sum(vals["semantic"]) / len(vals["semantic"])
    avg_all = (avg_nat + avg_sem) / 2
    print(f"{method:<12}{avg_nat:>18.2f}{avg_sem:>18.2f}{avg_all:>12.2f}")

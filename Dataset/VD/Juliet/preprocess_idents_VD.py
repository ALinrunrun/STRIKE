import json
import sys
sys.path.append('../../../python_parser')
from run_parser import get_identifiers_coda
from tqdm import tqdm


path = "train.jsonl"
list_1, list_0 = [], []

with open(path, "r", encoding="utf-8") as f:
    total_lines = sum(1 for _ in f)
    f.seek(0)  # Reset file pointer
    
    for line_num, line in enumerate(tqdm(f, total=total_lines, desc="Processing lines"), start=1):
        if not line.strip():
            continue  # skip space

        item = json.loads(line)
        func = item.get("func", "")
        target = item.get("target", "")
        idx = item.get("idx", "")
        
        variable_names1, function_names1, _ = get_identifiers_coda(func, "c")
        
        new_item = {
            "code1": func,
            "variable_name1": variable_names1,
            "function_name1": function_names1,
            "idx": idx
        }
        
        if target == 1 or target == "1":
            list_1.append(new_item)
        elif target == 0 or target == "0":
            list_0.append(new_item)
    
    new_data = {"1": list_1, "0": list_0}
    
    with open("processed_output.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)
    
    print(f"Extraction complete — {len(list_1)} positive samples and {len(list_0)} negative samples.")
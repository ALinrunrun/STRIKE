import json
import sys
sys.path.append('../../../python_parser')
from run_parser import get_identifiers_coda


path = "train_sampled.txt"
list_1, list_0 = [], []

with open(path, "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f, start=1):
        if not line.strip():
            continue  # skip space

        item = json.loads(line)
        func = item.get("func", "")
        target = item.get("target", "")
        idx = item.get("idx", "")
        
        variable_names1, function_names1, _ = get_identifiers_coda(func, "java")
        
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
    
    print(f"Extraction completed: {len(list_1)} positive samples and {len(list_0)} negative samples in total.")
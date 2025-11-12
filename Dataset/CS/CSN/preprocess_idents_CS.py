import json
import sys
sys.path.append('../../../python_parser')
from run_parser import get_identifiers_coda
from tqdm import tqdm


path = "train.jsonl"
list = []

with open(path, "r", encoding="utf-8") as f:
    total_lines = sum(1 for _ in f)
    f.seek(0)  # Reset file pointer

    for line_num, line in enumerate(tqdm(f, total=total_lines, desc="Processing lines"), start=1):
        if not line.strip():
            continue  # skip space

        item = json.loads(line)
        code = item.get("code", "")
        target = ' '.join(item.get("docstring_tokens", "")).replace('\n', '')
        target = ' '.join(target.strip().split())
        
        variable_names1, function_names1, _ = get_identifiers_coda(code, "java")
        
        new_item = {
            "source": code,
            "variable_name1": variable_names1,
            "function_name1": function_names1,
            "target": target
        }
        
        list.append(new_item)
    
    new_data = {"0": list}
    
    with open("processed_output.json", "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)
    
    print(f"Extraction complete — {len(list)} CS samples.")
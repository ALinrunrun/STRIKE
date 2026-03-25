import os
import sys
sys.path.append('../../../')
sys.path.append('../../../python_parser')
import json
import pandas as pd
import shutil
from utils import get_code_tokens_dataset

def get_adv_set(csv_path, model_name):

    index_to_target = {}

    with open("../CSN/test_sampled.jsonl", "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 1000:
                break
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            index_to_target[i] = (obj["docstring"], obj["docstring_tokens"])

    output_dir = os.path.dirname(csv_path)
    base_name = os.path.splitext(os.path.basename(csv_path))[0]
    adv_set_output_file = os.path.join(output_dir, f"test_data_{model_name}_{base_name}.jsonl")


    df = pd.read_csv(csv_path)

    df = df[["Index", "Original Code", "Adversarial Code", "Type"]]

    df = df[(df["Index"] >= 500) & (df["Index"] < 1000)]
    # df = df[df["Index"] < 1000]

    success_rows = df["Original Code"].notna() & (df["Original Code"].str.strip() != "")
    success_count = success_rows.sum()
    print(success_count)

    new_entries = []
    for Index, adv in zip(df.loc[success_rows, "Index"], df.loc[success_rows, "Adversarial Code"]):
        new_code_tokens = get_code_tokens_dataset(adv, "java")   
        new_entry = {
            "original_string": base_name,
            "language": "java",
            "code": adv,
            "code_tokens": new_code_tokens,
            "docstring": index_to_target[Index][0],
            "docstring_tokens": index_to_target[Index][1],
            "idx": 123456
        }
        new_entries.append(new_entry)

    with open(adv_set_output_file, "w", encoding="utf-8") as f:
        for entry in new_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        

folders = ["codebert", "codegpt", "codet5"]

for folder in folders:
    csv_files = [f for f in os.listdir(folder) if f.endswith(".csv")]
    print(f"\nFolder: {folder} — found {len(csv_files)} CSV files")

    for csv_file in csv_files:
        csv_path = os.path.join(folder, csv_file)
        print(f"csv_path: {csv_path}")
        try:
            get_adv_set(csv_path, folder)
        except Exception as e:
            print(f"[error] failed on {csv_path}")

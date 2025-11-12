import os
import json
import pandas as pd
import shutil



def get_adv_set(csv_path, model_name):

    index_to_target = {}

    with open("../test_sampled.jsonl", "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= 1000:
                break
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if "target" in obj:
                index_to_target[i] = obj["target"]

    output_dir = os.path.dirname(csv_path)
    base_name = os.path.splitext(os.path.basename(csv_path))[0]
    adv_set_output_file = os.path.join(output_dir, f"adv_by_{base_name}.jsonl")


    df = pd.read_csv(csv_path)

    df = df[["Index", "Original Code", "Adversarial Code", "Type"]]

    if "strike" in csv_path.lower():
        df = df[(df["Index"] >= 500) & (df["Index"] < 1000)]
    else:
        df = df[df["Index"] < 1000]

    success_rows = df["Original Code"].notna() & (df["Original Code"].str.strip() != "")
    success_count = success_rows.sum()
    print(success_count)

    new_entries = []
    for Index, adv in zip(df.loc[success_rows, "Index"], df.loc[success_rows, "Adversarial Code"]):   
        new_entry = {
            "project": "Strike",
            "commit_id": "adv",
            "target": index_to_target[Index],
            "func": adv,
            "idx": Index
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
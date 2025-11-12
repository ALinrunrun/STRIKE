import json
import pandas as pd
import shutil


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


models = ["codebert", "codegpt", "codet5"]
for model_name in models:

    adv_csv_file = f"{model_name}/attack_strike_all.csv"
    base_train_file = "../train.jsonl"
    adv_plus_output_file = f"train_plus_{model_name}.jsonl"

    shutil.copy(base_train_file, adv_plus_output_file)

    df = pd.read_csv(adv_csv_file)

    df = df[["Index", "Original Code", "Adversarial Code", "Type"]]

    df = df[df["Index"] < 500]
    success_rows = df["Type"].notna()
    for Index, adv in zip(df.loc[success_rows, "Index"], df.loc[success_rows, "Adversarial Code"]):   
        new_entry = {
            "project": "Strike",
            "commit_id": "adv",
            "target": index_to_target[Index],
            "func": adv,
            "idx": 123456
        }

        with open(adv_plus_output_file, "a", encoding="utf-8") as f:
            f.write("\n" + json.dumps(new_entry, ensure_ascii=False))
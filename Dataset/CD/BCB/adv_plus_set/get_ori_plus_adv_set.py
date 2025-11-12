import json
import pandas as pd
import shutil

index_to_target = {}

with open("../test_sampled.txt", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i >= 1000:
            break
        line = line.strip()
        url1, url2, label = line.split('\t')
        index_to_target[i] = (url1, url2, label)

models = ["codebert", "codegpt", "codet5"]
for model_name in models:

    adv_csv_file = f"{model_name}/attack_strike_all.csv"
    base_data_file = "../data.jsonl"
    base_train_file = "../train_sampled.txt"
    adv_data = f"data_{model_name}.jsonl"
    adv_txt = f"train_sampled_{model_name}.txt"

    shutil.copy(base_data_file, adv_data)
    shutil.copy(base_train_file, adv_txt)

    df = pd.read_csv(adv_csv_file)

    df = df[["Index", "Original Code", "Adversarial Code", "Type"]]

    df = df[df["Index"] < 500]
    success_rows = df["Original Code"].notna() & (df["Original Code"].str.strip() != "")
    for Index, adv in zip(df.loc[success_rows, "Index"], df.loc[success_rows, "Adversarial Code"]):   
        url1, url2, label = index_to_target[Index]
        idx =f"adv{url1}"
        new_entry = {
            "func": adv,
            "idx": idx,
        }

        with open(adv_data, "a", encoding="utf-8") as f:
            f.write("\n" + json.dumps(new_entry, ensure_ascii=False))

        with open(adv_txt, "a", encoding="utf-8") as f:
            f.write(f"\n{idx}\t{url2}\t{label}")
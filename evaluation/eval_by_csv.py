import torch
import os
from transformers import RobertaTokenizer, RobertaConfig, RobertaModel
import torch.nn.functional as F
import pandas as pd

device = "cuda" if torch.cuda.is_available() else "cpu"
model_name = "microsoft/graphcodebert-base"

config = RobertaConfig.from_pretrained(model_name)
config.add_pooling_layer = False  # not construct pooler layer
tokenizer = RobertaTokenizer.from_pretrained(model_name)
model = RobertaModel.from_pretrained(model_name, config=config).to(device)
model.eval()

def remove_empty_lines(code: str) -> str:
    lines = code.splitlines()
    non_empty = [line for line in lines if line.strip() != ""]
    return "\n".join(non_empty)

def get_cls_embedding(code: str):
    tokens = tokenizer(
        code,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=512
    ).to(device)

    with torch.no_grad():
        outputs = model(**tokens)
    # CLS（[batch, hidden_dim]）
    return outputs.last_hidden_state[:, 0, :]

def cosine_similarity(code1: str, code2: str) -> float:
    code1 = remove_empty_lines(code1)
    code2 = remove_empty_lines(code2)
    e1 = get_cls_embedding(code1)
    e2 = get_cls_embedding(code2)
    return F.cosine_similarity(e1, e2).item()

def eval_csv(csv_path, limit):
    df = pd.read_csv(csv_path)
    
    # Keep taget_col
    df = df[["Index", "Original Code", "Adversarial Code", "Query Times", "Time Cost", "Type"]]

    df = df[df["Index"] < limit]

    # ================== Begin cal ==================
    num_of_samples = len(df)
    success_rows = df["Type"].notna()
    # success_rows = df["Original Code"].notna() & (df["Original Code"].str.strip() != "")
    success_count = success_rows.sum()
    total_queries = df["Query Times"].sum()
    total_time = df["Time Cost"].sum()

    # Attack Success Rate
    asr = success_count / num_of_samples if num_of_samples > 0 else 0.0

    # Average Model Queries
    amq = total_queries / num_of_samples if num_of_samples > 0 else 0.0

    # Average Running Time
    art = total_time / num_of_samples if num_of_samples > 0 else 0.0

    # Average Code Similarity（Only succ)
    acs_list = []
    for orig, adv in zip(df.loc[success_rows, "Original Code"], df.loc[success_rows, "Adversarial Code"]):
        acs_list.append(cosine_similarity(orig, adv))
    acs = sum(acs_list) / len(acs_list) if acs_list else 0.0

    # ================== Output ==================
    print(f"ASR:    {success_count}/{num_of_samples} = {asr*100:.2f}%")
    print(f"AMQ:    {amq:.2f} queries/sample")
    print(f"ART:    {art:.2f} min/sample")
    print(f"ACS:    {acs*100:.2f}%")
    print(f"TotalTime:    {total_time:.2f}mins")

import sys
import glob

# Use the first command-line argument if provided; otherwise, default to 1000.
limit = int(sys.argv[1]) if len(sys.argv) > 1 else 1000


all_csv = glob.glob("eval_csv_place_foder/*.csv")

if not all_csv:
    print("No CSV files found in current directory.")
    sys.exit(0)

all_csv = sorted(all_csv)

for csv_path in all_csv:
    print("========================================")
    if not os.path.exists(csv_path):
        print(f"[skip] {csv_path} not found, skip.")
        continue

    print(f"csv_path: {csv_path}, limit: {limit}")
    try:
        eval_csv(csv_path, limit)
    except Exception as e:
        print(f"[error] eval_csv failed on {csv_path}: {e}")
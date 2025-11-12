# This folder contains the data preprocessing scripts used for generating the naturalness vocabulary shared across the baseline methods, including ALERT, BeamAttack, and ITGen.

import os

os.system("CUDA_VISIBLE_DEVICES=0 python get_substitutes_baseline.py \
    --store_path ./test_subs_vulnerability.jsonl \
    --base_model=microsoft/codebert-base-mlm \
    --eval_data_file ../../VD/Juliet/test_sampled.jsonl \
    --block_size 512 \
    --index 0 1000")

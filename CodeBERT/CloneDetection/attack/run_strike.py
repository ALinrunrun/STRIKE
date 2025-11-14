import os

os.system("CUDA_VISIBLE_DEVICES=1 python attack_strike.py \
    --levels=1234 \
    --output_dir=../orig_model \
    --model_type=roberta \
    --tokenizer_name=microsoft/codebert-base \
    --model_name_or_path=microsoft/codebert-base \
    --csv_store_path result/attack_strike_all.csv \
    --base_model=microsoft/codebert-base-mlm \
    --eval_data_file=../../../Dataset/CD/BCB/test_sampled.txt \
    --block_size 512 \
    --eval_batch_size 2 \
    --seed 123456")
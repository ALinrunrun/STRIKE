import os

os.system("CUDA_VISIBLE_DEVICES=1 python attack_strike.py \
    --levels=1234 \
    --output_dir=../orig_model \
    --model_type=gpt2 \
    --tokenizer_name=microsoft/CodeGPT-small-java-adaptedGPT2 \
    --model_name_or_path=microsoft/CodeGPT-small-java-adaptedGPT2 \
    --config_name=microsoft/CodeGPT-small-java-adaptedGPT2 \
    --csv_store_path result/attack_strike_gpt5_nano.csv \
    --base_model=microsoft/codebert-base-mlm \
    --eval_data_file=../../../Dataset/CD/BCB/test_sampled.txt \
    --block_size 512 \
    --eval_batch_size 2 \
    --seed 123456")
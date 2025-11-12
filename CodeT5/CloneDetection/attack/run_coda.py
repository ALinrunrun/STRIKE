import os

os.system("CUDA_VISIBLE_DEVICES=0 python attack_coda.py \
    --output_dir=../saved_models \
    --model_type=t5 \
    --tokenizer_name=Salesforce/codet5-base \
    --model_name_or_path=Salesforce/codet5-base \
    --csv_store_path result/attack_coda_all.csv \
    --base_model=microsoft/codebert-base-mlm \
    --eval_data_file=../../../Dataset/CD/BCB/test_sampled.txt \
    --block_size 512 \
    --eval_batch_size 2 \
    --seed 123456")

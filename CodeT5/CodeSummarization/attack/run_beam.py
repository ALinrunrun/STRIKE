import os

os.system("CUDA_VISIBLE_DEVICES=0 python attack_beam.py \
    --output_dir=../saved_models \
    --model_type=t5 \
    --tokenizer_name=Salesforce/codet5-base \
    --model_name_or_path=Salesforce/codet5-base \
    --csv_store_path result/attack_beam_all.csv \
    --eval_data_file=../../../Dataset/CS/CSN/test_sampled.jsonl \
    --block_size 512 \
    --eval_batch_size 2 \
    --max_source_length 256 \
    --max_target_length 128 \
    --beam_size 10 \
    --beam_size_num 5 \
    --seed 123456")
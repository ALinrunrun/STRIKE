import os

os.system("CUDA_VISIBLE_DEVICES=0 python run.py \
    --output_dir=../saved_models/ \
    --do_train \
    --do_eval \
    --model_type roberta \
    --model_name_or_path microsoft/codebert-base \
    --train_filename=../../../Dataset/CS/CSN/adv_plus_set/train_plus_codebert.jsonl \
    --dev_filename=../../../Dataset/CS/CSN/valid.jsonl \
    --test_filename=../../../Dataset/CS/CSN/test.jsonl \
    --max_source_length 256 \
    --max_target_length 128 \
    --beam_size 10 \
    --train_batch_size 32 \
    --eval_batch_size 32 \
    --learning_rate 5e-5 \
    --num_train_epochs 10 \
    2>&1")


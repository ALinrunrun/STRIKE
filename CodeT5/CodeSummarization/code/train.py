import os

os.system("CUDA_VISIBLE_DEVICES=0 python run.py \
    --output_dir=../saved_models/ \
    --model_type=t5 \
    --model_name_or_path=Salesforce/codet5-base \
    --tokenizer_name=Salesforce/codet5-base \
    --do_train \
    --do_eval \
    --train_filename=../../../Dataset/CS/CSN/adv_plus_set/train_plus_codet5.jsonl \
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


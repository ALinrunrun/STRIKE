import os

os.system("CUDA_VISIBLE_DEVICES=0 python run.py \
    --output_dir=../saved_models/ \
    --model_type=roberta \
    --config_name=microsoft/codebert-base \
    --model_name_or_path=microsoft/codebert-base \
    --tokenizer_name=roberta-base \
    --do_test \
    --train_data_file=../../../Dataset/CD/BCB/train_sampled.txt \
    --eval_data_file=../../../Dataset/CD/BCB/valid_sampled.txt \
    --test_data_file=../../../Dataset/CD/BCB/test_sampled.txt \
    --epoch 2 \
    --block_size 400 \
    --train_batch_size 16 \
    --eval_batch_size 32 \
    --learning_rate 5e-5 \
    --max_grad_norm 1.0 \
    --evaluate_during_training \
    --seed 123456 2>&1")


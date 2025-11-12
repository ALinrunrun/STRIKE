import os

os.system("CUDA_VISIBLE_DEVICES=0 python run.py \
    --output_dir=../saved_models/ \
    --model_type=t5 \
    --config_name=Salesforce/codet5-base \
    --model_name_or_path=Salesforce/codet5-base \
    --tokenizer_name=codet5-base \
    --do_train \
    --train_data_file=../../../Dataset/CD/BCB/adv_plus_set/train_sampled_codet5.txt \
    --eval_data_file=../../../Dataset/CD/BCB/valid_sampled.txt \
    --test_data_file=../../../Dataset/CD/BCB/test_sampled.txt \
    --epoch 2 \
    --block_size 256 \
    --train_batch_size 4 \
    --eval_batch_size 8 \
    --learning_rate 5e-5 \
    --max_grad_norm 1.0 \
    --evaluate_during_training \
    --seed 123456")
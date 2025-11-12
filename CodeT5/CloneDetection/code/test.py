import os

os.system("CUDA_VISIBLE_DEVICES=0 python run.py \
    --output_dir=../saved_models/ \
    --model_type=t5 \
    --config_name=Salesforce/codet5-base \
    --model_name_or_path=Salesforce/codet5-base \
    --tokenizer_name=codet5-base \
    --do_test \
    --train_data_file=../../../Dataset/CD/BCB/train_sampled.txt \
    --eval_data_file=../../../Dataset/CD/BCB/valid_sampled.txt \
    --test_data_file=../../../Dataset/CD/BCB/adv_plus_set/codebert/adv_by_attack_strike_all.txt \
    --epoch 2 \
    --block_size 400 \
    --train_batch_size 16 \
    --eval_batch_size 32 \
    --learning_rate 5e-5 \
    --max_grad_norm 1.0 \
    --evaluate_during_training \
    --seed 123456")
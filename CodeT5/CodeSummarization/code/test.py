import os

os.system("CUDA_VISIBLE_DEVICES=1 python run.py \
    --do_test \
    --load_model_path ../saved_models/checkpoint-best-bleu/pytorch_model.bin \
    --model_type=t5 \
    --model_name_or_path=Salesforce/codet5-base \
    --tokenizer_name=Salesforce/codet5-base \
    --train_filename=../../../Dataset/CS/CSN/train.jsonl \
    --dev_filename=../../../Dataset/CS/CSN/valid.jsonl \
    --test_filename=../../../Dataset/CS/CSN/test.jsonl \
    --output_dir ../saved_models/ \
    --max_source_length 256 \
    --max_target_length 128 \
    --beam_size 10 \
    --train_batch_size 32 \
    --eval_batch_size 32 \
    --learning_rate 5e-5 \
    --num_train_epochs 10 \
    --seed 123456  2>&1")

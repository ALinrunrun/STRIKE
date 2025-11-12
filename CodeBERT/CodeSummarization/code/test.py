import os

os.system("CUDA_VISIBLE_DEVICES=1 python run.py \
    --output_dir=../saved_models/ \
    --model_type=roberta \
    --tokenizer_name=microsoft/codebert-base \
    --model_name_or_path=microsoft/codebert-base \
    --load_model_path=../saved_models/checkpoint-best-bleu/pytorch_model.bin \
    --do_test \
    --train_filename=../../../Dataset/CS/CSN/train.jsonl \
    --dev_filename=../../../Dataset/CS/CSN/valid.jsonl \
    --test_filename=../../../Dataset/CS/CSN/test.jsonl \
    --max_source_length 256 \
    --max_target_length 128 \
    --beam_size 10 \
    --train_batch_size 32 \
    --eval_batch_size 32 \
    --learning_rate 5e-5 \
    --num_train_epochs 10 \
    --seed 123456 2>&1")

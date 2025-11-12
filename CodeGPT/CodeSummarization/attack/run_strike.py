import os

os.system("CUDA_VISIBLE_DEVICES=1 python attack_strike.py \
    --output_dir=../orig_model \
    --model_type=gpt2 \
    --model_name_or_path microsoft/CodeGPT-small-java-adaptedGPT2 \
    --csv_store_path result/attack_strike_gpt5_nano.csv \
    --eval_data_file=../../../Dataset/CS/CSN/test_sampled.jsonl \
    --load_model_path=../orig_model/checkpoint-best-bleu/pytorch_model.bin \
    --eval_batch_size 2 \
    --block_size 512 \
    --max_source_length 256 \
    --max_target_length 128 \
    --beam_size 10 \
    --seed 123456")
# coding=utf-8
'''For attacking CodeBERT models'''
import os
import re
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import json
import sys
from datetime import datetime
sys.path.append('../../../')
sys.path.append('../code')
sys.path.append('../../../python_parser')
retval = os.getcwd()

import logging
import argparse
import warnings
import torch
import time
import random
from utils import get_code_tokens
from model import Model
from utils import set_seed, build_vocab
from utils import Recorder
from run import TextDataset
from run_parser import get_identifiers
from attacker import get_code_pairs
from ITGenAttacker import ITGen_Attacker
from transformers import RobertaForMaskedLM
from transformers import (GPT2Config, GPT2Model, GPT2Tokenizer, RobertaTokenizer)

warnings.simplefilter(action='ignore', category=FutureWarning)  # Only report warning

MODEL_CLASSES = {
    'gpt2': (GPT2Config, GPT2Model, GPT2Tokenizer)
}

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser()

    ## Required parameters
    parser.add_argument("--output_dir", default=None, type=str, required=True,
                        help="The output directory where the model predictions and checkpoints will be written.")

    ## Other parameters
    parser.add_argument("--eval_data_file", default=None, type=str,
                        help="An optional input evaluation data file to evaluate the perplexity on (a text file).")
    parser.add_argument("--test_data_file", default=None, type=str,
                        help="An optional input evaluation data file to evaluate the perplexity on (a text file).")
    parser.add_argument("--base_model", default=None, type=str,
                        help="Base Model")
    parser.add_argument("--model_type", default="bert", type=str,
                        help="The model architecture to be fine-tuned.")
    parser.add_argument("--model_name_or_path", default=None, type=str,
                        help="The model checkpoint for weights initialization.")
    parser.add_argument("--csv_store_path", default=None, type=str,
                        help="Base Model")
    parser.add_argument("--use_ga", action='store_true',
                        help="Whether to GA-Attack.")
    parser.add_argument("--mlm", action='store_true',
                        help="Train with masked-language modeling loss instead of language modeling.")
    parser.add_argument("--mlm_probability", type=float, default=0.15,
                        help="Ratio of tokens to mask for masked language modeling loss")

    parser.add_argument("--config_name", default="", type=str,
                        help="Optional pretrained config name or path if not the same as model_name_or_path")
    parser.add_argument("--tokenizer_name", default="", type=str,
                        help="Optional pretrained tokenizer name or path if not the same as model_name_or_path")
    parser.add_argument("--cache_dir", default="", type=str,
                        help="Optional directory to store the pre-trained models downloaded from s3 (instread of the default one)")
    parser.add_argument("--block_size", default=-1, type=int,
                        help="Optional input sequence length after tokenization."
                             "The training dataset will be truncated in block of this size for training."
                             "Default to the model max input length for single sentence inputs (take into account special tokens).")
    parser.add_argument("--do_train", action='store_true',
                        help="Whether to run training.")
    parser.add_argument("--do_eval", action='store_true',
                        help="Whether to run eval on the dev set.")
    parser.add_argument("--do_test", action='store_true',
                        help="Whether to run eval on the dev set.")
    parser.add_argument("--evaluate_during_training", action='store_true',
                        help="Run evaluation during training at each logging step.")
    parser.add_argument("--eval_batch_size", default=4, type=int,
                        help="Batch size per GPU/CPU for evaluation.")
    parser.add_argument('--seed', type=int, default=42,
                        help="random seed for initialization")
    parser.add_argument('--beam_size', type=int, default=3,
                        help="beam_size")
    args = parser.parse_args()

    device = torch.device("cuda")
    args.device = device

    # Set seed
    set_seed(args.seed)
    
    config_class, model_class, tokenizer_class = MODEL_CLASSES[args.model_type]
    config = config_class.from_pretrained(args.config_name if args.config_name else args.model_name_or_path,
                                          cache_dir=args.cache_dir if args.cache_dir else None)
    config.num_labels = 2
    tokenizer = tokenizer_class.from_pretrained(args.tokenizer_name,
                                                do_lower_case=False,
                                                cache_dir=args.cache_dir if args.cache_dir else None)
    if args.block_size <= 0:
        args.block_size = tokenizer.max_len_single_sentence  # Our input block size will be the max possible for the model
    args.block_size = min(args.block_size, tokenizer.max_len_single_sentence)
    if args.model_name_or_path:
        model = model_class.from_pretrained(args.model_name_or_path,
                                            from_tf=bool('.ckpt' in args.model_name_or_path),
                                            config=config,
                                            cache_dir=args.cache_dir if args.cache_dir else None)
    else:
        model = model_class(config)

    model = Model(model, config, tokenizer, args)

    load_model_path = '../saved_models/checkpoint-best-f1/model.bin'
    model.load_state_dict(torch.load(load_model_path), strict=False)
    print("{} - reload model from {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), load_model_path))

    model.to(args.device)

    codebert_mlm = RobertaForMaskedLM.from_pretrained("microsoft/codebert-base-mlm")
    tokenizer_mlm = RobertaTokenizer.from_pretrained("microsoft/codebert-base-mlm")
    codebert_mlm.to('cuda')
    
    # Load Dataset
    ## Load Dataset
    eval_dataset = TextDataset(tokenizer, args, args.eval_data_file)
    ## Load code pairs
    source_codes = get_code_pairs(args.eval_data_file, tokenizer, args)
    
    subs_path = "../../../Dataset/preprocess/backup/test_subs_clone.jsonl"
    generated_substitutions = []
    
    with open(subs_path) as f:
        for line in f:
            js = json.loads(line.strip())
            generated_substitutions.append(js["substitutes"])
    assert len(source_codes) == len(eval_dataset) == len(generated_substitutions)
    
    success_attack = 0
    total_cnt = 0
    recoder = Recorder(args.csv_store_path)
    attacker = ITGen_Attacker(args, model, tokenizer)
    start_time = time.time()
    query_times = 0
    for index, example in enumerate(eval_dataset):
        # if index > 5:
        #     break
        print("Index: ", index)
        example_start_time = time.time()
        code_pair = source_codes[index]
        logits, preds = model.get_results([example], args.eval_batch_size)
        orig_label = preds[0]
        true_label = example[1].item()
        if not orig_label == true_label:
            continue
            
        substitutes = generated_substitutions[index]
        first_code = code_pair[2]
        
        orig_code_tokens = get_code_tokens(first_code)
        identifiers = list(substitutes.keys())
        if len(identifiers) == 0:
            continue  
        total_cnt += 1      
        
        adv_code, is_success, replaced_words = attacker.itgen_attack(example, substitutes, code_pair, query_times, logits, example_start_time)
        attack_type = "itgen"
        
        example_end_time = (time.time() - example_start_time) / 60
        print("Example time cost: ", round(example_end_time, 2), "min")
        print("ALL examples time cost: ", round((time.time() - start_time) / 60, 2), "min")
        print("Query times in this attack: ", model.query - query_times)
        
        replace_info = ''
        if replaced_words is not None:
                for key in replaced_words.keys():
                    replace_info += key + ':' + replaced_words[key] + ','
  
        if is_success == 1:
            success_attack += 1
            recoder.write(index, code_pair[2], adv_code, len(orig_code_tokens), len(identifiers),
                          replace_info, model.query - query_times, example_end_time, attack_type)
        else:
            recoder.write(index, None, None,
                      len(orig_code_tokens), len(identifiers),
                      None, model.query - query_times, example_end_time, None)
        query_times = model.query

        print("Success rate: {}/{} = {}".format(success_attack, total_cnt, 1.0 * success_attack / total_cnt))
    print("Final success rate: {}/{} = {}".format(success_attack, total_cnt, 1.0 * success_attack / total_cnt))


if __name__ == '__main__':
    main()
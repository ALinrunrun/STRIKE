import sys
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
sys.path.append('../../../')
sys.path.append('../code')
sys.path.append('../../../python_parser')

from torch.utils.data import DataLoader, SequentialSampler
from run import TextDataset, convert_examples_to_features
from attacker import get_new_example
import numpy as np
import math
np.set_printoptions(suppress=True)

import torch
import copy
import pandas as pd
import bleu
import time
from tqdm import tqdm
from typing import List
import hashlib
import gc
from strike_parser import (
    ast_has_error,
    get_perturbed_code,
    extract_statement_blocks,
    extract_reorderable_blocks,
    merge_code,
)
from utils import CodeDataset, _tokenize
from run_parser import get_identifiers_coda, get_example_batch
from scipy.spatial.distance import cosine as cosine_distance
ADOPT_GPT5 = True
if ADOPT_GPT5:
    from gpt5_client import GPT5Client
    gpt5 = GPT5Client(max_workers=20)

# ========== Global parameter settings ==========
STATEMENT_LLM_ITER_CONSTRUCTION = 10
STATEMENT_CANS_NUM = 5
WORD_LLM_ITER_CONSTRUCTION = 5  # make sure enough, prevent no candicates
WORD_CANS_NUM = 30
MAX_SEQ_LEN = 512
NUMBER_1 = 256
NUMBER_2 = 32
FIXED_LABEL = 0

LEVEL_1 = [
    """Insert 1–4 lines of additional code into this Java control flow structures — preferably reusing existing variables or objects — so that it resembles code a developer might temporarily insert for internal checks or variable inspection, even the creation of temporary variables. Preserve the original code exactly when inserting, add only new lines, and return the full modified code without any explanations or comments.
"""
]
LEVEL_2 = [
    """Convert this Java control structure, with the main change applied to the control handle, into a semantically equivalent alternative. Return only the complete modified code, without any explanations or comments.
"""
]
LEVEL_3 = [
    """Reorder the lines in the following code snippet that do not depend on each other. Return only the reordered version of the original code snippet — do not add, remove, or modify any lines, and include no explanations or comments.
"""
]
TEMPLATES = [LEVEL_1, LEVEL_2, LEVEL_3]

def get_embeddings(code, variables, tokenizer_mlm, codebert_mlm):
    new_code = copy.deepcopy(code)
    chromesome = {}
    for i in variables:
        chromesome[i] = '<unk>'
    new_code = get_example_batch(new_code, chromesome, "java")
    _, _, code_tokens = get_identifiers_coda(new_code, "java")
    processed_code = " ".join(code_tokens)
    words, sub_words, keys = _tokenize(processed_code, tokenizer_mlm)
    sub_words = [tokenizer_mlm.cls_token] + sub_words[:512 - 2] + [tokenizer_mlm.sep_token]
    input_ids_ = torch.tensor([tokenizer_mlm.convert_tokens_to_ids(sub_words)])
    with torch.no_grad():
        embeddings = codebert_mlm.roberta(input_ids_.to('cuda'))[0]

    return embeddings

class Strike_Attacker(object):
    def __init__(self, args, model_tgt, tokenizer_tgt, tokenizer_mlm, model_mlm, bleu_file, tokenizer_llm, model_llm, fasttext_model, generated_substitutions):
        self.args = args
        self.model_tgt = model_tgt
        self.tokenizer_tgt = tokenizer_tgt
        self.tokenizer_mlm = tokenizer_mlm
        self.model_mlm = model_mlm
        self.bleu_file = bleu_file
        self.tokenizer_llm = tokenizer_llm
        self.model_llm = model_llm
        self.query = 0
        self.fasttext_model = fasttext_model
        self.substitutions = generated_substitutions

    def cosine_similarity(self, code_1: str, code_2: str):

        code1_ids = self.tokenizer_mlm.encode(code_1, truncation=True, max_length=self.args.block_size)
        code2_ids = self.tokenizer_mlm.encode(code_2, truncation=True, max_length=self.args.block_size)

        code1_tensor = torch.tensor(code1_ids, dtype=torch.long, device=self.args.device).unsqueeze(0)
        code2_tensor = torch.tensor(code2_ids, dtype=torch.long, device=self.args.device).unsqueeze(0)

        with torch.no_grad():
            emb1 = self.model_mlm(code1_tensor)[0]
            emb2 = self.model_mlm(code2_tensor)[0]

        # Use mean pooling (average all token embeddings)
        emb1 = emb1.mean(dim=1)   # -> [1, hidden_size]
        emb2 = emb2.mean(dim=1)

        # Compute cosine similarity
        sim = torch.cosine_similarity(emb1, emb2).item()

        return sim

    def get_llm_feedback(self, level_of_prompt, code, chunks):
        res_lists = []
        generated = None
        if level_of_prompt in (0, 1, 2):
            for prompt in TEMPLATES[level_of_prompt]:
                if ADOPT_GPT5:
                    all_prompts = []
                    for code_ref in chunks:
                        code_snippet, start, end, indent_len = code_ref
                        # get all prompts, 10 time a snippet
                        prompts = []
                        full_prompt = prompt + "java code snippet:\n" + code_snippet
                        for _ in range(STATEMENT_LLM_ITER_CONSTRUCTION):
                            prompts.append(full_prompt)
                        all_prompts.append(prompts)
                    gpt5_fb = gpt5.get_gpt5_feedback(all_prompts, lang="java")
                    
                for index, code_ref in tqdm(
                    enumerate(chunks),
                    total=len(chunks),
                    desc="Generating candidates snippet lists",
                    leave=False,
                    file=sys.stderr,
                    ncols=100
                ):
                    code_snippet, start, end, indent_len = code_ref
                    if ADOPT_GPT5:
                        generated = gpt5_fb[index]
                    else:
                        # get all prompts, 10 time a snippet
                        prompts = []
                        full_prompt = prompt + "java code snippet:\n" + code_snippet
                        for _ in range(STATEMENT_LLM_ITER_CONSTRUCTION):
                            prompts.append(full_prompt)

                        # query the llm and get answers
                        max_new_tokens = 1024
                        generated = self.query_model(prompts, int(max_new_tokens), divide=True)

                    candidates_code_list = []
                    candidates_scored = []
                    for content in generated:
                        content = content.strip()
                        if ADOPT_GPT5:
                            answer = content 
                        else: 
                            if "GPT4 Correct Assistant:" not in content:
                                continue 
                            answer = content.split("GPT4 Correct Assistant:", 1)[1].strip()

                        if "[ERROR]" in answer:
                            continue 
                        
                        if "java code snippet:" in answer.lower():
                            lines = answer.splitlines(keepends=True)
                            new_snippet = "".join(lines[1:])
                        else:
                            new_snippet = answer

                        lines = new_snippet.splitlines(keepends=True)
                        if lines and lines[0].lstrip().startswith("```"):
                            if lines[-1].strip().startswith("```"):
                                new_snippet = "".join(lines[1:-1])
                            else:
                                new_snippet = "".join(lines[1:])
                        sim = self.cosine_similarity(code_snippet, new_snippet)
                        candidates_scored.append((new_snippet, sim))
                    unique_scored = {}
                    for snippet, sim in candidates_scored:
                        temp_code, _ = merge_code(
                            code, new_snippet, start, end, indent_len
                        )
                        if ast_has_error(temp_code):
                            # print("[Skip invalid snippet]")
                            continue
                        key = hashlib.md5(snippet.strip().encode("utf-8")).hexdigest()
                        if key not in unique_scored or sim > unique_scored[key][1]:
                            unique_scored[key] = (snippet, sim)
                    candidates_scored = list(unique_scored.values())
                    # print(len(candidates_scored))
                    candidates_scored.sort(key=lambda t: t[1], reverse=True)
                    candidates_code_list = [s for s, _ in candidates_scored[:STATEMENT_CANS_NUM]]
                    # candidates_code_so = [s for _, s in candidates_scored[:STATEMENT_CANS_NUM]]
                    for i in candidates_code_list:
                        print(i)
                        print("----------")
                    res_lists.append(candidates_code_list)
                    if generated is not None:
                        del generated
                    torch.cuda.empty_cache()
                    gc.collect() 
        else:
            pass
        return res_lists

    def query_model(self, prompts: List[str], max_gen_tokens: int, divide: bool = False) -> List[str]:
        res = []
        sub_lists = []
        if divide:
            sub_lists = [prompts[i : i + 10] for i in range(0, len(prompts), 10)]
        else:
            sub_lists.append(prompts)
        for sub_list in sub_lists:
            messages = [[{"role": "user", "content": prompt}] for prompt in sub_list]
            inputs = self.tokenizer_llm.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
                padding=True,
            ).to(self.model_llm.device)

            attention_mask = (
                inputs["attention_mask"] if "attention_mask" in inputs else None
            )

            with torch.no_grad():
                outputs = self.model_llm.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=attention_mask,
                    do_sample=True,
                    temperature=0.5,
                    max_new_tokens=max_gen_tokens,
                    num_return_sequences=1,
                )
            decoded = self.tokenizer_llm.batch_decode(outputs, skip_special_tokens=True)
            res += decoded
        return res

    def eval_bleu(self, example):
        self.query += 1
        bleu_file = self.bleu_file
        model = self.model_tgt
        tokenizer = self.tokenizer_tgt
        eval_features = convert_examples_to_features([example], tokenizer, self.args, stage='test')
        eval_data = TextDataset(eval_features, self.args)

        # Calculate bleu
        eval_sampler = SequentialSampler(eval_data)
        eval_dataloader = DataLoader(eval_data, sampler=eval_sampler, batch_size=self.args.eval_batch_size)

        model.eval()
        p = []
        for batch in eval_dataloader:
            batch = tuple(t.to(self.args.device) for t in batch)
            inputs, labels, attn_mask, loss_mask = batch
            with torch.no_grad():
                preds = model(inputs=inputs, labels=labels, attn_mask=attn_mask, loss_mask=loss_mask, pred=True)
                for pred in preds:
                    t = pred[0].cpu().numpy()
                    t = list(t)
                    if 0 in t:
                        t = t[:t.index(0)]
                    text = tokenizer.decode(t, clean_up_tokenization_spaces=False)
                    p.append(text)

        pre_summary = p[0]
        model.train()
        predictions = []
        if os.path.exists(bleu_file + "/dev.output"):
            os.remove(bleu_file + "/dev.output")
        if os.path.exists(bleu_file + "/dev.gold"):
            os.remove(bleu_file + "/dev.gold")
        with open((bleu_file + "/dev.output"), 'w') as f, open((bleu_file + "/dev.gold"), 'w') as f1:
            for ref, gold in zip(p, [example]):
                predictions.append(str(gold.idx) + '\t' + ref)
                f.write(str(gold.idx) + '\t' + ref + '\n')
                f1.write(str(gold.idx) + '\t' + gold.target + '\n')
        f.close()
        f1.close()
        try:
            (goldMap, predictionMap) = bleu.computeMaps(predictions, bleu_file + "/dev.gold")
            dev_bleu = round(bleu.bleuFromMaps(goldMap, predictionMap)[0], 2)
        except:
            dev_bleu = -1

        return dev_bleu, pre_summary, example.target

    def adaptive_beam_search(self, example, base_prob, base_code, alt_lists, chunks, init_k=3):
        idx = example.idx
        nl = example.target
        
        ori_pos={}
        for i, snippet_list in enumerate(alt_lists):
            _, start, end, indent_len = chunks[snippet_list[0]]
            ori_pos[i]=(start, end, indent_len)
        
        beam = [(base_prob, base_code, ori_pos, [])]  # (prob, code, delta, path)
        beam_width = init_k
        miss_rounds = 0

        best_bleu, best_code = base_prob, base_code
        best_path = []

        while beam:
            # print("========")
            # for i in beam:
            #     _, o, m, n = i
            #     print(o)
            #     print(m,n)
            new_candidates = []
            improved = False
            
            for _, code, pos, path in beam[:beam_width]:
                for i, snippet_list in enumerate(alt_lists):
                    if snippet_list is None or i in path:
                        continue
                    for new_snippet in snippet_list[1]:
                        if not new_snippet or not new_snippet.strip():
                            continue
                        start, end, indent_len = pos[i]
                        temp_code, temp_delta = merge_code(
                            code, new_snippet, start, end, indent_len
                        )
                        new_example = get_new_example(idx, temp_code, nl)
                        pred_bleu, pre_summary, ref_summary = self.eval_bleu(new_example[0])
                        if pred_bleu == 0.0:
                            return {
                                "success": True,
                                "code": temp_code,
                                "prob": pred_bleu,
                                "path": path + [i],
                            }
                        
                        if pred_bleu < best_bleu:
                            improved = True
                            best_bleu, best_code = pred_bleu, temp_code
                            best_path = path + [i]
                            
                        new_pos = copy.deepcopy(pos)
                        for j in range(i + 1, len(new_pos)):
                            x, y, z = new_pos[j]
                            new_pos[j] = (x + temp_delta, y + temp_delta, z)
                        
                        new_candidates.append((pred_bleu, temp_code, new_pos, path + [i]))
           
            if improved:
                miss_rounds = 0
                beam_width = init_k
            else:
                miss_rounds += 1
                if miss_rounds >= 2:
                    beam_width = max(1, beam_width - 1)

            # --- Update the beam ---
            beam = sorted(new_candidates, key=lambda x: x[0])[:beam_width]

        return {
            "success": False,
            "code": best_code,
            "prob": best_bleu,
            "path": best_path,
        }

    def greedy_search_idents(self, example, base_prob, base_code, alt_lists):
        idx = example.idx
        nl = example.target
        
        greedy = False
        candidate = None
        remove_ident = None
        best_bleu, best_code = base_prob, base_code
        # print(alt_lists)
        
        for item, candidates in alt_lists.items():
            if candidates is None:
                continue
            for new_candidate in candidates:
                temp_code = get_perturbed_code(base_code, item, new_candidate)
                new_example = get_new_example(idx, temp_code, nl)
                pred_bleu, pre_summary, ref_summary = self.eval_bleu(new_example[0])
                if pred_bleu == 0.0:
                    greedy = True
                    return {
                        "greedy": greedy,
                        "success": True,
                        "code": temp_code,
                        "prob": pred_bleu,
                        "remove": item,
                        "candidate": new_candidate,
                    }
                if pred_bleu < best_bleu:
                    greedy = True
                    remove_ident = item
                    candidate = new_candidate
                    best_bleu, best_code = pred_bleu, temp_code

        if not greedy:
            for item, candidates in alt_lists.items():
                if candidates is None or len(candidates) == 0:
                    continue
                # print(candidates)
                remove_ident = item
                candidate = candidates[0]
                best_code = get_perturbed_code(base_code, item, candidate)
                break
        return {
            "greedy": greedy,
            "success": False,
            "code": best_code,
            "prob": best_bleu,
            "remove": remove_ident,
            "candidate": candidate,
        }

    def strike_attack(self, original_bleu, example, selected_levels):
        code = example.source
        
        cur_code = code
        last_prob = original_bleu
        cur_prob = original_bleu
        print(cur_code)
        
        final_res = {
            "success": False,
            "end_type": [],
            "idents": [],
            "code": code,
            "prob": original_bleu,
            "llm_query_time": 0
        }
        
                
        for level_of_prompt in selected_levels:
            if final_res["success"]:
                break
            
            if level_of_prompt in (0, 1, 2):                
                last_prob = cur_prob

                if level_of_prompt == 0:
                    chunks = extract_statement_blocks(cur_code)
                    chunks += extract_reorderable_blocks(cur_code)
                    chunks = sorted(chunks, key=lambda x: x[1])
                elif level_of_prompt == 1:
                    chunks = extract_statement_blocks(cur_code)
                else:
                    chunks = extract_reorderable_blocks(cur_code)
                
                if len(chunks) == 0:
                    print(
                        f">> CTN_{level_of_prompt+1}! (N/A -> SKIP)"
                    )
                    continue
                final_res["end_type"].append(level_of_prompt+1)
                query_start_time = time.time()
                res_lists = self.get_llm_feedback(level_of_prompt, cur_code, chunks)
                query_end_time = time.time()
                final_res["llm_query_time"] += query_end_time-query_start_time
                # for i in res_lists:
                #     print("=========================")
                #     for x in i:
                #         print(x)
                res_lists = [(i, v) for i, v in enumerate(res_lists)]
                result = self.adaptive_beam_search(
                    example, cur_prob, cur_code, res_lists, chunks
                )
                path = result["path"]
                cur_prob = result["prob"]
                cur_code = result["code"]
                print(cur_code)

                if result["success"]:
                    final_res["success"] = True
                    print(
                        f">> SUC_{level_of_prompt+1}! ({last_prob:8f} -> {cur_prob:8f} {path})"
                    )
                    break
                else:
                    delay = last_prob - cur_prob
                    print(
                        f">> CTN_{level_of_prompt+1}! ({last_prob:8f} -> {cur_prob:8f} = ↓{delay:8f} {path})"
                    )
            elif level_of_prompt == 3:
                last_prob = cur_prob

                variable_names1, function_names1, _ = get_identifiers_coda(code, "java")
                
                random_subs = []
                for i in np.random.choice(self.substitutions[str(FIXED_LABEL)], size=len(self.substitutions[str(FIXED_LABEL)]), replace=False):
                    if len(i['variable_name1']) < len(variable_names1):
                        continue
                    temp = copy.deepcopy(i)
                    random_subs.append(temp)
                    if len(random_subs) >= NUMBER_1:
                        break
                substituions = []
                ori_embeddings1 = get_embeddings(cur_code, variable_names1+function_names1, self.tokenizer_mlm, self.model_mlm)
                
                ori_embeddings1 = torch.nn.functional.pad(ori_embeddings1, [0, 0, 0, 512 - np.shape(ori_embeddings1)[1]])
                

                embeddings_leng = np.shape(ori_embeddings1)[-1]
                cos = torch.nn.CosineSimilarity(dim=1, eps=1e-6)
                for sub in random_subs:
                    embeddings1 = get_embeddings(sub['source'], [], self.tokenizer_mlm, self.model_mlm)
                    embeddings1 = torch.nn.functional.pad(embeddings1, [0, 0, 0, 512 - np.shape(embeddings1)[1]])
                    cos_d = np.sum(cos(ori_embeddings1, embeddings1).cpu().numpy()) / embeddings_leng
                    substituions.append(([sub['variable_name1'], sub['function_name1'], sub['source']], cos_d))

                substituions = sorted(substituions, key=lambda x: x[1], reverse=False)
                substituions = [x[0] for x in substituions[:NUMBER_2]]
                temp_subs_variable_name = set()
                temp_subs_function_name = set()
                subs_code = []
                for subs in substituions:
                    for i in subs[0]:
                        temp_subs_variable_name.add(i)
                    for i in subs[1]:
                        temp_subs_function_name.add(i)
                    subs_code.append(subs[2])

                subs_variable_name = []
                subs_function_name = []
                for i in temp_subs_variable_name:
                    subs_variable_name.append([i, self.fasttext_model.get_word_vector(i)])
                for i in temp_subs_function_name:
                    subs_function_name.append([i, self.fasttext_model.get_word_vector(i)])
                
                substituions = {}
                for i in variable_names1:
                    temp = []
                    i_vec = self.fasttext_model.get_word_vector(i)
                    for j in subs_variable_name:
                        if i == j[0]:
                            continue
                        temp.append([j[0], 1 - cosine_distance(i_vec, j[1])])
                    temp = sorted(temp, key=lambda x: x[1], reverse=True)[:WORD_CANS_NUM]
                    substituions[i] = [x[0] for x in temp]
                for i in function_names1:
                    temp = []
                    i_vec = self.fasttext_model.get_word_vector(i)
                    for j in subs_function_name:
                        if i == j[0]:
                            continue
                        temp.append([j[0], 1 - cosine_distance(i_vec, j[1])])
                    temp = sorted(temp, key=lambda x: x[1], reverse=True)[:WORD_CANS_NUM]
                    substituions[i] = [x[0] for x in temp]
                
                substitutes = substituions
                
                identifiers = list(substitutes.keys())
                if len(identifiers) == 0:
                    print(
                        f">> CTN_{level_of_prompt+1}! (N/A -> SKIP)"
                    )
                    continue
                final_res["end_type"].append(level_of_prompt+1)
                print(f"identifiers: {identifiers}")
                
                unconfir_snippets = len(substitutes)
                early_trigger = unconfir_snippets - min(
                    unconfir_snippets,
                    max(1, int(math.sqrt(unconfir_snippets)) + 1)
                )
                last_level_prob_sum = 0
                early_stop_flag = 0
                max_fail_streak = 2
                while unconfir_snippets > 0:
                    result = self.greedy_search_idents(example, cur_prob, cur_code, substitutes)
                    
                    greedy = result["greedy"]
                    remove_ident = result["remove"]
                    replaced_ident = result["candidate"]
                    cur_prob = result["prob"]
                    cur_code = result["code"]
                    final_res["idents"].append(f"{remove_ident}:{replaced_ident}")
                    
                    if result["success"]:
                        final_res["success"] = True
                        print(
                            f">> SUC_{level_of_prompt+1}! ({last_prob:8f} -> {cur_prob:8f}) | {remove_ident} => {replaced_ident}"
                        )
                        print(cur_code)
                        break
                    else:
                        cur_level_prob_sum = last_prob - cur_prob
                        level_delay = cur_level_prob_sum - last_level_prob_sum
                        last_level_prob_sum = cur_level_prob_sum
                        print(
                            f">> ↓{level_delay:.6f} | {remove_ident} => {replaced_ident}"
                        )
                        substitutes[remove_ident] = None
                        unconfir_snippets -= 1
                    if not greedy:
                        early_stop_flag += 1
                        if early_stop_flag == max_fail_streak:
                            # print("(greedy early stop)", end="")
                            break
                    else:
                        early_stop_flag == 0
                    
                    if unconfir_snippets <= early_trigger:
                        cur_drop = last_prob - cur_prob
                        if cur_drop < last_prob * 0.01:
                            break

                if not final_res["success"]:
                    delay = last_prob - cur_prob
                    print(
                        f">> CTN_{level_of_prompt+1}! ({last_prob:8f} -> {cur_prob:8f} = ↓{delay:8f})"
                    )
                    print(cur_code)
            else:
                print(f">> NO_{level_of_prompt+1} pass...")
                continue
        
        final_res["prob"] = cur_prob
        final_res["code"] = cur_code
        return final_res
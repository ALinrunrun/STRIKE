# filename: gpt5_client.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from tqdm import tqdm  

class GPT5Client:
    def __init__(self, max_workers=10):
        self.client = OpenAI()
        self.max_workers = max_workers

    def _query_once(self, i, input_text, instructions):
        resp = self.client.responses.create(
            model="gpt-5-nano",
            instructions=instructions,
            input=input_text,
        )
        # print(f"--- Response {i} ---")
        # print(resp.output_text)
        return resp.output_text

    def get_gpt5_feedback(self, input_text, lang):
        if lang == "java":
            instructions="You are an automated assistant that produces semantically equivalent Java code variants. Output only code, no explanations."
        elif lang == "c":
            instructions="You are an automated assistant that produces semantically equivalent C code variants. Output only code, no explanations."
        else:
            instructions=f"You are an automated assistant that produces semantically equivalent {lang} code variants. Output only code, no explanations."
        
        flat_prompts = []
        index_map = []
        for group_idx, group in enumerate(input_text):
            for prompt in group:
                flat_prompts.append(prompt)
                index_map.append(group_idx)

        
        total = len(flat_prompts)
        flat_results = [None] * len(flat_prompts)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._query_once, i, text, instructions): i
                for i, text in enumerate(flat_prompts)
            }
            with tqdm(total=total, desc="Collecting GPT-5 responses", ncols=100, leave=False,) as pbar:
                for f in as_completed(futures):
                    idx = futures[f]
                    try:
                        flat_results[idx] = f.result()
                    except Exception as e:
                        flat_results[idx] = f"[ERROR] {e}"
                    pbar.update(1)
        
        grouped_results = [[] for _ in range(len(input_text))]
        for result, group_idx in zip(flat_results, index_map):
            grouped_results[group_idx].append(result)
            
        return grouped_results


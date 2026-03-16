# STRIKE

![License](https://img.shields.io/badge/License-MIT-green.svg)

- [Overview](#overview)
    - [Attack Approach](#attack-approach)
    - [Folder Structure](#folder-structure)
- [Experiments](#experiments)
    - [Environment Configuration](#environment-configuration)
    - [Model Fine-tuning and Evaluation](#model-fine-tuning-and-evaluation)
    - [Data Preprocess](#data-preprocess)
    - [Running Experiments](#running-experiments)
    - [Evaluate Experiments](#evaluate-experiments)
    - [Robustness Enhancement Experiment](#robustness-enhancement-experiment)
    - [Human Evaluation](#human-evaluation)
    - [Ablation Study](#ablation-study)
    - [LLM Replacement Validation](#llm-replacement-validation)
    - [Hyperparameter Sensitivity Analysis](#hyperparameter-sensitivity-analysis)

# Overview
## Attack Approach

- [ALERT](https://github.com/soarsmu/attack-pretrain-models-of-code/)
- [BeamATTACK](https://github.com/CGCL-codes/Attack_PTMC)
- [CODA](https://github.com/tianzhaotju/CODA)
- [ITGen](https://github.com/unknownhl/ITGen)

## Folder Structure
```
├── README.md
├── requirements.txt
├── strike_parser.py
├── gpt5_client.py
├── utils.py
├── CodeBERT
│   ├── CloneDetection
│   │   ├── attack
│   │   │   ├── ITGenAttacker.py
│   │   │   ├── attack_alert.py
│   │   │   ├── attack_beam.py
│   │   │   ├── attack_coda.py
│   │   │   ├── attack_itgen.py
│   │   │   ├── attack_strike.py
│   │   │   ├── attacker.py
│   │   │   ├── beamAttacker.py
│   │   │   ├── codaAttacker.py
│   │   │   ├── result
│   │   │   ├── run_alert.py
│   │   │   ├── run_beam.py
│   │   │   ├── run_coda.py
│   │   │   ├── run_itgen.py
│   │   │   ├── run_strike.py
│   │   │   └── strikeAttacker.py
│   │   └── code
│   │       ├── model.py
│   │       ├── run.py
│   │       ├── test.py
│   │       └── train.py
│   ├── CodeSummarization
│   │   ├── attack
│   │   └── code
│   └── VulnerabilityDetection
│       ├── attack
│       └── code
├── CodeGPT
├── CodeT5
├── Dataset
│   ├── CD
│   │   └── BCB
│   │       ├── adv_plus_set
│   │       │   ├── codebert
│   │       │   ├── codegpt
│   │       │   ├── codet5
│   │       │   ├── get_adv_set.py
│   │       │   └── get_ori_plus_adv_set.py
│   │       └── preprocess_idents_CD.py
│   ├── CS
│   ├── VD
│   └── preprocess
│       ├── backup
│       │   ├── get_substitutes_baseline.py
│       │   └── run_baseline_get_subs.py
│       └── split_testset.py
├── algorithms
├── evaluation
│   ├── eval_by_csv.py
│   └── eval_csv_place_foder
├── human_evaluation
│   ├── README.md
│   ├── eval.py
│   ├── requirement.txt
│   └── selected_samples.json
├── python_parser
│   ├── parser_folder
│   │   ├── tree-sitter-c
│   │   ├── tree-sitter-java
│   │   ├── tree-sitter-python
│   │   ├── utils.py
│   ├── run_parser.py
└── END
```


## Dataset and Model
All datasets and fine-tuned model checkpoints used in our experiments are publicly available at [Figshare](https://doi.org/10.6084/m9.figshare.30598091.v1) to facilitate replication and further research.

# Experiments
***We use CodeBERT - Clone Detection as an example to demonstrate how all experiment scripts are executed.***

## Environment Configuration

```
pip install -r requirements.txt
```

## Model Fine-tuning and Evaluation
We fine-tune the pre-trained model on the dataset of the target task to achieve better performance, and save the resulting checkpoint at `./saved_models/checkpoint-best-f1/model.bin`.
This produces the CodeBERT model fine-tuned for the Clone Detection task.

### Fine-tuning

Navigate to the target folder, Modify the parameters in `train.py` and run.
```
cd CodeBERT/CloneDetection/Code
```
```
import os

os.system("CUDA_VISIBLE_DEVICES=1 python run.py \ 
    --output_dir=../saved_models/ \
    --model_type=roberta \
    --config_name=microsoft/codebert-base \
    --model_name_or_path=microsoft/codebert-base \
    --tokenizer_name=roberta-base \
    --do_train \
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
```
```
python train.py
```
### Evaluation

Evaluate the performance of the fine-tuned model, modify the parameters in `test.py` and run.
```
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
```
```
python test.py
```
## Data Preprocess
To support vocabulary generation, we preprocess the data by classifying labels and extracting identifiers for the identifier-stage verification. The processed output is stored in `./processed_output.json_CD`, which contains data organized by label categories.

Step1. Navigate to the target folder .
```
cd Dataset\CD\BCB
```

Step2. Run the preprocessing script

```
python preprocess_idents_CD.py
```

## Running Experiments

**You can conveniently run any tool, including STRIKE, from the project root:**

```bash
cd CodeBERT/CloneDetection/attack
python run_xxx.py
```
The `run_xxx.py` here can be `run_alert.py`, `run_beam.py`, `run_itgen.py`, `run_coda.py`, `run_strike.py`

Take `run_strike.py`  as an example:

```
import os

os.system("CUDA_VISIBLE_DEVICES=1 python attack_strike.py \
    --levels=1234 \
    --output_dir=../orig_model \
    --model_type=roberta \
    --tokenizer_name=microsoft/codebert-base \
    --model_name_or_path=microsoft/codebert-base \
    --csv_store_path result/attack_strike_all.csv \
    --base_model=microsoft/codebert-base-mlm \
    --eval_data_file=../../../Dataset/CD/BCB/test_sampled.txt \
    --block_size 512 \
    --eval_batch_size 2 \
    --seed 123456")
```

This generates a `.csv` file containing multiple adversarial perturbation results.

**CSV Format**
The output CSV contains **9 columns**. Each column is described below:
- **Index** — Sample index, ranging from `0` to `3999`.
- **Original Code** — The original input code before the attack.
- **Adversarial Code** — The adversarial sample generated after a successful attack.
- **Program Length** — The code length measured in tokens.
- **Identifier Num** — The number of identifiers extracted from the code.
- **Replaced Identifiers** — Details of identifier replacements performed during the attack (if applicable).
- **Query Times** — The number of model queries made for that specific attack.
- **Time Cost** — Time consumed for the attack, in minutes.
- **Type** — `0` or empty when the attack failed; otherwise a string describing the successful attack (examples: `ALERT` with its mode like `GA` or `greedy`, or `STRIKE` listing which components were perturbed).

**Parameters:**
--levels  
    Specifies which components are enabled  
    Level 1 → Dead Code Insertion  
    Level 2 → Control Structure Replacement  
    Level 3 → Statement Reordering  
    Level 4 → Identifier Perturbation  

--csv_store_path  
    Specifies the path to save intermediate results

--eval_data_file
    Point to the dataset you want to attack.

## Evaluate Experiments
You can place the file you want to evaluate (the CSV file generated by `run_xxx.py`) into `evaluation/eval_csv_place_folder/`, and then simply run:
```
cd evaluation
python eval_by_csv.py <Limit>
```
where {Limit} specifies the maximum index to read (e.g., 1000 means reading all entries with Index < 1000).

## Robustness Enhancement Experiment
We prepare a subset S covering indices 0–999 for robustness verification, and split it into S1 (indices 0–499) and S2 (indices 500–999). You can use the split tool `split_testset.py` to extract these subsets.

```
cd Dataset\preprocess\
python split_testset.py <input_file> <total_count> <step>
```
Next, run `run_xxx.py` to obtain `.csv` result files for each tool on the current model and task using the Ssubset. Then place all generated CSV files into the corresponding folder `Dataset/{TASK}/{DATASET}/adv_plus_set/{TARGET_MODEL}/`
Note: you must update the `--eval_data_file` argument to point to the new dataset subset you want to attack.

Finall, run `get_ori_plus_adv_set.py` and `get_adv_set.py`.
```
cd Dataset\CD\BCB\adv_plus_set
python get_ori_plus_adv_set.py
python get_adv_set.py
```
The first script `get_ori_plus_adv_set.py` generates a new combined training set that merges the original training data with the adversarial samples produced by **STRIKE** for each model.
The second script `get_adv_set.py` generates the adversarial test sets containing only the successfully attacked samples for each tool and model.

We then use the `combined training sets` produced by the first script to fine-tune, use the original models,
and evaluate their performance using the `adversarial test sets` generated by the second script. For detailed training and evaluation instructions, please refer [Model Fine-tuning and Evaluation](#model-fine-tuning-and-evaluation)

## Human Evaluation
To assess the naturalness and semantic similarity of generated adversarial samples, we conducted a human evaluation study.
The full questionnaire, instructions, and evaluation interface are provided in the **`human_evaluation/`** folder.
Participants were asked to score each perturbed code sample on contextual naturalness and semantic similarity following the standardized evaluation protocol included in this directory.

## Ablation Study
We adopt a well-structured modular architecture (see [Running Experiments](#running-experiments) for reference).
You can conveniently perform ablation studies by adjusting the value of `--level` in `run_strike.py`, which controls which components are activated during the attack or perturbation process.

Example:
```
--levels=234
--levels=134
```

## LLM Replacement Validation

We designed dedicated modules for the LLM substitution verification experiment across each model and task. You may configure the experiment by modifying the model loader in `gpt5_client.py` and switching the global flag `ADOPT_GPT5` in `strikeAttacker.py` from `FALSE` to `TRUE`.
```
ADOPT_GPT5 = TRUE
```

## Hyperparameter Sensitivity Analysis

For the hyperparameter sensitivity analysis, we continued to use a convenient parameter-modification approach for testing. Still using CodeBERT-Clone Detection (CD) as an example, we opened the `strikeAttacker.py` script. In the global parameter section, the following configuration can be found:

```
cd CodeBERT\CloneDetection\attack
<open> strikeAttacker.py
```

```
# ========== Global parameter settings ==========
STATEMENT_LLM_ITER_CONSTRUCTION = 10 #1
STATEMENT_CANS_NUM = 5 #1
WORD_LLM_ITER_CONSTRUCTION = 5  # make sure enough, prevent no candicates
WORD_CANS_NUM = 30 #3
MAX_SEQ_LEN = 512
NUMBER_1 = 256 #2
NUMBER_2 = 32 #2

STRUC_BEAM = 3 #4
STRUC_EARLY_STOP = 3 #5
IDENT_EARLY_STOP = 2 #6
```

## Example of Adversarial Code Generation Pipeline

![Example](LLM4DCM.png)

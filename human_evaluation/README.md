# Human Evaluation - README

***Note: Due to CSV file writing, `\n` may be stored as `real line breaks`, causing some adversarial samples to display incorrectly. Please `ignore` this during evaluation.***

## 1. Overview

This tool provides a graphical user interface (GUI) for human evaluation of paired code samples.

* Left side: **Original code**
* Right side: **Adversarial (attacked) code**
* Includes **syntax highlighting** and **GitHub-style diff** to visualize code differences.
* **Diff View Mode:**  
  - 🟩 *Green lines* — Added or changed code  
  - 🟥 *Red lines* — Deleted code  

You will rate each code pair based on two criteria: **Naturalness** and **Semantic Similarity**.

## 2. Evaluation Criteria

**(1) Contextual Naturalness**  
Evaluates whether perturbations remain developer-like and contextually consistent, capturing the repetitive and predictable patterns characteristic of natural code.

**(2) Semantic Similarity**  
Evaluates whether the sample still preserves the original semantics.

## 3. Rating Scale (1–5 Likert)

1 = Very unsatisfied
2 = Unsatisfied
3 = Neutral
4 = Satisfied
5 = Very satisfied

## 4. How to Use

Step 1 — Install dependencies

    pip install -r requirements.txt

Step 2 — Run the evaluation tool

    python eval.py

Step 3 — Enter your username when prompted.  
    
    A file `<username>_results.json` will be created automatically to store your scores.

Step 4 — Rate all samples
    Check both panels and the diff view, then rate each code pair (1–5) for:

    * Naturalness
    * Semantic correctness

    Use “Save and Next” to move through samples.

## 5. Output Format
All results are saved in JSON:

## 5. Summarize the evaluation results
```
python summarize_eval_res.py
```
# End of Guide — Thank you for participating!











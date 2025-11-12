# Human Evaluation - README

## 1. Overview

This tool provides a graphical user interface (GUI) for human evaluation of paired code samples.

* Left side: **Original code**
* Right side: **Adversarial (attacked) code**
* Includes **syntax highlighting** and **GitHub-style diff** to visualize code differences.
* **Diff View Mode:**  
  - 🟩 *Green lines* — Added or changed code  
  - 🟥 *Red lines* — Deleted code  

You will rate each code pair based on two criteria: **Naturalness** and **Semantic Preservation**.

## 2. Evaluation Criteria

**(1) Naturalness**  
Evaluate whether the modifications appear human-written and contextually coherent.

**(2) Semantic Preservation**  
Evaluate hether the modified code still expresses the same functionality as the original.

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









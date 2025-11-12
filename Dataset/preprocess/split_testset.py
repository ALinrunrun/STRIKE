
# This script splits a large .jsonl (or .txt, .csv, etc.) file into smaller chunks,
# each containing a fixed number of lines.

# Useful for batch processing, inference, or distributed jobs.
# Command format:
# python split_testset.py <input_file> <total_count> <step>

# EXAMPLE:
# python split_testset.py Dataset/CS/CSN/test_sampled.jsonl 4000 1000
# test_sampled_0_1000.jsonl
# test_sampled_1000_2000.jsonl
# test_sampled_2000_3000.jsonl
# test_sampled_3000_4000.jsonl

# python split_testset.py CD/BCB/test_sampled.txt 1000 500
# test_sampled_0_500.txt
# test_sampled_500_1000.txt


import sys
import os

if len(sys.argv) != 4:
    print("Usage: python split_jsonl.py <input_file> <total_count> <step>")
    sys.exit(1)

input_file = sys.argv[1]
total = int(sys.argv[2])
step = int(sys.argv[3])

name, ext = os.path.splitext(input_file)

with open(input_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

total = min(total, len(lines))

for start in range(0, total, step):
    end = min(start + step, total)
    output_file = f"{name}_{start}_{end}{ext}"
    with open(output_file, "w", encoding="utf-8") as f_out:
        f_out.writelines(lines[start:end])
    print(f"wrote {end - start} lines → {output_file}")

print("Done......")
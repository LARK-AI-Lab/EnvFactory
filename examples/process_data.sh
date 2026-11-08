# Process sft dataset
python src/utils/data_process.py \
    --folders '["data","data1","data2"]' \
    --sft_output_path sft.json \
    --shuffle \
    --enable_think \
    --enable_skip \

# Process rl dataset (slime JSONL, consumed by scripts/slime/run_grpo.sh; all rows train, BFCL v3 evaluates)
python src/utils/data_process.py \
    --folders '["data_1", "data_2", "data_3"]' \
    --rl_output_path data/rl_train_fixed.jsonl \

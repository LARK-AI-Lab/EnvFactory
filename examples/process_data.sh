# Process sft dataset
python src/utils/data_process.py \
    --folders '["data","data1","data2"]' \
    --sft_output_path sft.json \
    --shuffle \
    --enable_think \
    --enable_skip \

# Process rl dataset (slime JSONL, consumed by scripts/slime/run_grpo.sh)
python src/utils/data_process.py \
    --folders '["data_1", "data_2", "data_3"]' \
    --rl_output_train_path data/rl_train.jsonl \
    --rl_output_val_path data/rl_val.jsonl \
    --train_val_split_ratio 0.95 \
    --shuffle \
# Process sft dataset
python src/utils/data_process.py \
    --folders '["data","data1","data2"]' \
    --sft_output_path sft.json \
    --shuffle \
    --enable_think \
    --enable_skip \

# Process rl dataset
python src/utils/data_process.py \
    --folders '["data_1", "data_2", "data_3"]' \
    --rl_output_train_path rl_train.json \
    --rl_output_val_path rl_val.json \
    --train_val_split_ratio 0.95 \
    --shuffle \
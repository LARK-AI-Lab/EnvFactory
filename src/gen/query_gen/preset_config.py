# Preset Configurations for Trajectories Sythesis
from src.gen.query_gen import QueryGenConfig

# SFT trajectories without user interaction
SFT_NON_CONV = QueryGenConfig(
    model_name = "sglang",
    pass_k = 4,
    max_iterations = 10,
    max_solve_iterations = 15,
    enable_split_turns = False,
    enable_query_refinement = False,
    enable_user_interaction = False,
    enable_user_tool_use = False,
    enable_user_verification = False,
    enable_filteration = False,
    enable_log_thinking_content = True,
    save_folder = "data_sft_non_conv",
    log_folder = "log_sft_non_conv",
)

# SFT trajectories without user interaction
SFT_CONV = QueryGenConfig(
    model_name = "sglang",
    pass_k = 4,
    max_iterations = 10,
    max_solve_iterations = 15,
    enable_split_turns = False,
    enable_query_refinement = True,
    enable_user_interaction = True,
    enable_user_tool_use = True,
    enable_user_verification = False,
    enable_filteration = False,
    enable_log_thinking_content = True,
    save_folder = "data_sft_conv",
    log_folder = "log_sft_conv",
)

# RL trajectories
RL_NON_CONV = QueryGenConfig(
    model_name = "deepseek",
    pass_k = 4,
    max_iterations = 10,
    max_solve_iterations = 15,
    enable_split_turns = False,
    enable_query_refinement = False,
    enable_user_interaction = False,
    enable_user_tool_use = False,
    enable_user_verification = False,
    enable_filteration = True,
    enable_log_thinking_content = True,
    save_folder = "data_rl_non_conv",
    log_folder = "log_rl_non_conv",
)
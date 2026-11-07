import os
import json
import argparse
import random
from typing import List, Dict, Any, Tuple
from collections import Counter
from src.utils.utils import SYSTEM_PROMPT, RL_SYSTEM_PROMPT
import traceback

INPUT_ROLES = {"user", "tool_response"}
OUTPUT_ROLES = {"assistant", "tool_call"}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--folders', type=json.loads, default=["data"])
    parser.add_argument('--sft_output_path', type=str)
    parser.add_argument('--rl_output_train_path', type=str)
    parser.add_argument('--rl_output_val_path', type=str)
    parser.add_argument('--verl_rl_path', type=str, help='Convert a verl-format RL json (e.g. LARK-Lab/EnvFactory-RL) instead of --folders.')
    parser.add_argument('--verl_rl_val_path', type=str, help='Held-out verl-format RL json; when set, --verl_rl_path is not split and all of it is training data.')
    parser.add_argument('--rl_exclude_envs', type=json.loads, default=["ClinicalTrialsGov"], help='Drop RL rows using these environments (network-bound).')
    parser.add_argument('--max_num', type=int)
    parser.add_argument('--train_val_split_ratio', type=float, default=0.9)
    parser.add_argument('--shuffle', action='store_true', default=False)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--enable_think', action='store_true', default=False)
    parser.add_argument('--enable_skip', action='store_true', default=False)
    parser.add_argument('--enable_plot', action='store_true', default=False)
    parser.add_argument('--plot_dir', type=str, default='plots')
    return parser.parse_args()

def load_tool_chains(folders: List[str], max_num: int = None, enable_skip: bool = False) -> List[Dict[str, Any]]:
    tool_chains = []
    incomplete_count = 0

    for folder in folders:
        if not os.path.exists(folder):
            continue

        for file in os.listdir(folder):
            if not file.endswith('.json'):
                continue
            if max_num and len(tool_chains) >= max_num:
                break

            filepath = os.path.join(folder, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                nodes = data["nodes"]

                if enable_skip:
                    # At least 2 turns
                    # All turns have tool calls                    
                    valid_turns = 0
                    do_skip = False
                    
                    for node in nodes:
                        if node.get("decision") is True:
                            valid_turns += 1
                        
                        # if not any(step["role"] == "tool_call" for step in node["steps"]):
                        #     do_skip = True
                        #     break
                    
                    if do_skip or valid_turns < 2:
                        incomplete_count += 1
                        continue

                mcp_servers = set()
                for node in nodes:
                    if node["mcp_servers"]:
                        mcp_servers.update(node["mcp_servers"])

                tool_chain = {
                    "nodes": nodes,
                    "seed": data.get("seed"),
                    "user_tools": data.get("user_tools"),
                    "mcp_servers": mcp_servers,
                }
                tool_chains.append(tool_chain)
            except Exception as e:
                traceback.print_exc()
                print(f"❌ Failed to load {filepath}: {e}")
                
        if max_num and len(tool_chains) >= max_num:
            break
                
    print(f"✅ Loaded {len(tool_chains)} valid tool chains")
    print(f"⚠️ Skipped {incomplete_count} incomplete tool chains")
    return tool_chains

def split_tool_chains(tool_chains: List[Dict[str, Any]], split_ratio: float = 0.95, shuffle: bool = False, seed: int = 42) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split tool chains into train and validation sets by conversation."""
    if not tool_chains:
        return [], []
    
    # Apply shuffle if requested
    if shuffle:
        random.seed(seed)
        random.shuffle(tool_chains)
        print(f"✅ Shuffled {len(tool_chains)} tool chains with seed {seed}")
    
    # Calculate split index
    split_idx = int(len(tool_chains) * split_ratio)
    
    # Split the tool chains
    train_chains = tool_chains[:split_idx]
    val_chains = tool_chains[split_idx:]
    
    print(f"✅ Split {len(tool_chains)} tool chains into {len(train_chains)} train and {len(val_chains)} validation")
    return train_chains, val_chains

def calculate_tool_chain_stats(tool_chains: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistics from loaded tool chains for plotting."""
    stats = {
        'turn_distribution': Counter(),
        'steps_per_turn_distribution': Counter(),
        'tool_calls_per_turn_distribution': Counter(),
        'steps_per_conversation_distribution': Counter(),
        'user_interactions_per_turn_distribution': Counter(),
        'mcp_server_distribution': Counter(),
    }
    
    def count_pairs(steps):
        """Count complete pairs in steps."""
        tool_calls = 0
        user_interactions = 0
        roles = [s.get('role', '') for s in steps]
        
        i = 0
        while i < len(roles) - 1:
            if roles[i] == 'tool_call' and roles[i + 1] == 'tool_response':
                tool_calls += 1
                i += 2
            else:
                i += 1
        
        i = 0
        while i < len(roles) - 1:
            if roles[i] == 'assistant' and roles[i + 1] == 'user':
                user_interactions += 1
                i += 2
            else:
                i += 1
        
        return tool_calls, user_interactions
    
    for chain in tool_chains:
        conv_total_steps = 0
        
        for node in chain["nodes"]:
            if not node.get("decision") or not node.get("steps"):
                break
            
            steps = node["steps"]
            tool_calls, user_interactions = count_pairs(steps)
            num_steps = tool_calls + user_interactions
            
            conv_total_steps += num_steps
            
            stats['steps_per_turn_distribution'][num_steps] += 1
            stats['tool_calls_per_turn_distribution'][tool_calls] += 1
            stats['user_interactions_per_turn_distribution'][user_interactions] += 1
        
        if conv_total_steps > 0:
            stats['steps_per_conversation_distribution'][conv_total_steps] += 1
            stats['turn_distribution'][conv_total_steps] += 1
        
        for mcp in chain["mcp_servers"]:
            stats['mcp_server_distribution'][mcp] += 1
    
    return stats

def format_step(step: Dict[str, Any]) -> str:
    """Format a single step into text representation."""
    role, content = step['role'], step.get('content', '')
    assert content is not None, f"Got None content for role {role}"
    
    if role == 'user' or role == 'assistant':
        return str(content)
    elif role == 'tool_response':
        return ''.join(f"<tool_response>\n{tr}\n</tool_response>\n" for tr in content)
    elif role == 'tool_call':
        tool_calls = []
        for tc in content:
            tool_call = {"name": tc["name"], "arguments": tc["arguments"]}
            tool_calls.append(f"<tool_call>\n{json.dumps(tool_call)}\n</tool_call>\n")
        return ''.join(tool_calls)
    else:
        raise ValueError

def validate_steps(steps: List[Dict], node_idx: int) -> None:
    """Validate step alternation and roles."""
    for i, step in enumerate(steps):
        expected_roles = INPUT_ROLES if i % 2 == 0 else OUTPUT_ROLES
        if step['role'] not in expected_roles:
            raise ValueError(f"Node {node_idx} Step {i}: Expected {expected_roles}, got '{step['role']}'")

def is_failed_tool_call(steps: List[Dict], output_idx: int) -> bool:
    cur_step = steps[output_idx]
    if cur_step.get('role') != 'tool_call':
        return False

    if output_idx + 1 >= len(steps):
        return False
    
    next_step = steps[output_idx + 1]
    if next_step.get('role') != 'tool_response':
        return False
    
    # Check tool_response content for "Fail" or "Error" or is user tool
    content = next_step.get('content', [])
    if any('Fail' in tr or 'Error' in tr for tr in content):
        return True
    return False

def convert_to_sft_data(tool_chains: List[Dict[str, Any]], output_path: str, shuffle: bool = False, seed: int = 42, enable_think: bool = True) -> None:
    """Convert tool chains to SFT format (one sample per step pair)."""
    from src.manager.mcp_client_manager import MCPManager

    all_samples, valid_count, invalid_count = [], 0, 0
    
    for chain in tool_chains:
        try:
            tools = MCPManager.filter_tools(chain["mcp_servers"])
            user_tools = chain.get("user_tools") or []
            user_tool_names = [t["name"] for t in user_tools]
            assistant_tools = [t for t in tools if t["function"]["name"] not in user_tool_names]

            # Prepare system prompt
            system = SYSTEM_PROMPT
            if user_tools:
                user_tools_text = "- Here are the actions you may instruct the user to do:\n"
                user_tools_text += "\n".join(f"{t['name']}: {t['description']}" for t in user_tools)
                system = system.replace("{user_tools}", user_tools_text)
            else:
                system = system.replace("{user_tools}", "")
            system = system.replace("{tools}", "\n".join(json.dumps(t) for t in assistant_tools))

            history = []
            for node_idx, node in enumerate(chain["nodes"]):
                if not node.get("decision") or not node.get("steps"):
                    break

                steps = node["steps"]
                validate_steps(steps, node_idx)

                # Skip this turn if no tool calls in this turn
                if not any(step["role"] == "tool_call" for step in node["steps"]):
                    continue

                # Process step pairs
                for i in range(0, len(steps)-1, 2):  # Skip last if odd
                    input_step, output_step = steps[i], steps[i + 1]
                    
                    input_text = format_step(input_step)
                    output_text = format_step(output_step)
                    output_step_type = output_step.get("type", "KEEP")

                    if enable_think:
                        think = f"<think>{output_step.get('think', '')}</think>\n\n" if 'think' in output_step else ""
                    else:
                        think = ""

                    if output_step_type == "REMOVE":
                        continue

                    # Filter out failed tool calls
                    if (not is_failed_tool_call(steps, i+1)) and (output_step_type == "KEEP"):
                        all_samples.append({
                            "instruction": input_text.strip(),
                            "input": "",
                            "output": think + output_text,
                            "system": system,
                            "history": [h.copy() for h in history],
                        })
                    
                    history.append([input_text, output_text])
            
            if history:
                valid_count += 1

        except Exception as e:
            invalid_count += 1
            traceback.print_exc()
            print(f"⚠️ SFT conversion error (seed {chain.get('seed')}): {e}")

    _save_json(all_samples, output_path, valid_count, invalid_count, "SFT", shuffle=shuffle, seed=seed)

def _rl_row(prompt: List[Dict], tool_calls: List[Dict], envs: List[str], initial_state: Dict, final_state: Dict) -> Dict:
    """One slime RL row; see src/rollout/slime/generate.py for the consumer."""
    return {
        "prompt": [{"role": "system", "content": RL_SYSTEM_PROMPT}] + prompt,
        "label": json.dumps(tool_calls, ensure_ascii=False),
        "metadata": {"envs": envs, "initial_state": initial_state, "final_state": final_state},
    }

def _keep_rl_row(row: Dict, exclude_envs: List[str]) -> bool:
    metadata = row["metadata"]
    return (
        json.loads(row["label"]) != []
        and all(env in metadata["initial_state"] for env in metadata["envs"])
        and not set(metadata["envs"]) & set(exclude_envs)
    )

def convert_to_rl_data(tool_chains: List[Dict[str, Any]], output_path: str, exclude_envs: List[str] = ()) -> None:
    """Convert tool chains to slime RL rows (one sample per node)."""
    all_samples, valid_count, invalid_count = [], 0, 0

    QWEN3_ROLE_MAPPING = {
        "user": "user",
        "assistant": "assistant",
        "tool_call": "assistant",
        "tool_response": "user",
    }
    
    for chain in tool_chains:
        try:
            history = []
            for node_idx, node in enumerate(chain["nodes"]):
                if not node.get("decision") or not node.get("steps"):
                    break
                
                query = node["query"].strip()
                prompt = history + [{"role": QWEN3_ROLE_MAPPING["user"], "content": query}]
                tool_calls = [
                    {"name": tool_call["name"], "arguments": tool_call["arguments"], "masked_arguments": tool_call.get("masked_arguments", [])} 
                    for step in node["steps"] 
                    if step['role'] == "tool_call" 
                    for tool_call in step['content']
                ] # tool calls for this turn

                rl_sample = _rl_row(
                    prompt, tool_calls, node.get("mcp_servers", []),
                    node.get("initial_scenario", {}), node.get("final_scenario", {}),
                )
                if _keep_rl_row(rl_sample, exclude_envs):
                    all_samples.append(rl_sample)
                
                for step in node["steps"]:
                    history.append({
                        "role": QWEN3_ROLE_MAPPING[step["role"]], 
                        "content": format_step(step)
                    })


            valid_count += 1
        except Exception as e:
            invalid_count += 1
            traceback.print_exc()
            print(f"⚠️ RL conversion error (seed {chain.get('seed')}): {e}")
    
    _save_jsonl(all_samples, output_path, valid_count, invalid_count, "RL")

def load_verl_rl_data(path: str, exclude_envs: List[str] = ()) -> List[Dict]:
    """Convert the previous verl RL format (e.g. LARK-Lab/EnvFactory-RL) to slime rows."""
    with open(path, 'r', encoding='utf-8') as f:
        rows = json.load(f)
    samples = []
    for row in rows:
        kwargs = row["extra_info"]["mcp_factory_kwargs"]
        sample = _rl_row(
            json.loads(row["prompt"]), json.loads(row["reward_model"]["ground_truth"]),
            json.loads(kwargs["mcp_servers"]), json.loads(kwargs["initial_config"]), json.loads(kwargs["final_config"]),
        )
        if _keep_rl_row(sample, exclude_envs):
            samples.append(sample)
    print(f"✅ Converted {len(samples)} / {len(rows)} verl RL rows from {path}")
    return samples

def split_rl_rows(rows: List[Dict], split_ratio: float, shuffle: bool = False, seed: int = 42) -> Tuple[List[Dict], List[Dict]]:
    """Split RL rows by conversation: rows of one conversation share their opening user message."""
    conversations = {}
    for row in rows:
        conversations.setdefault(json.dumps(row["prompt"][1], sort_keys=True), []).append(row)
    train, val = split_tool_chains(list(conversations.values()), split_ratio, shuffle=shuffle, seed=seed)
    return [row for conv in train for row in conv], [row for conv in val for row in conv]

def _save_json(data: List[Dict], path: str, valid: int, invalid: int, label: str, shuffle: bool = False, seed: int = 42) -> None:
    if shuffle:
        random.seed(seed)
        random.shuffle(data)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved {len(data)} {label} samples to {path} (valid: {valid}, invalid: {invalid})")

def _save_jsonl(data: List[Dict], path: str, valid: int, invalid: int, label: str) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        for row in data:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"✅ Saved {len(data)} {label} samples to {path} (valid: {valid}, invalid: {invalid})")

def main():
    args = parse_args()
    if args.verl_rl_path:
        # Rows are already RL samples; slime reshuffles them every epoch (--rollout-shuffle).
        rows = load_verl_rl_data(args.verl_rl_path, args.rl_exclude_envs)
        if args.verl_rl_val_path:
            train_rows, val_rows = rows, load_verl_rl_data(args.verl_rl_val_path, args.rl_exclude_envs)
        else:
            train_rows, val_rows = split_rl_rows(rows, args.train_val_split_ratio, shuffle=args.shuffle, seed=args.seed)
        _save_jsonl(train_rows, args.rl_output_train_path, len(train_rows), 0, "RL")
        _save_jsonl(val_rows, args.rl_output_val_path, len(val_rows), 0, "RL")
        return

    tool_chains = load_tool_chains(args.folders, args.max_num, args.enable_skip)
    
    if args.enable_plot:
        print("📊 Generating plots...")
        from src.utils.plot import generate_plots
        stats = calculate_tool_chain_stats(tool_chains)
        generate_plots(stats, args.plot_dir, plot_types=['turns_steps', 'tool_calls_user_interactions', 'sunburst'])
        print(f"✅ Plots saved to {args.plot_dir}")
    
    if args.sft_output_path:
        convert_to_sft_data(tool_chains, args.sft_output_path, shuffle=args.shuffle, seed=args.seed, enable_think=args.enable_think)

    if args.rl_output_train_path and args.rl_output_val_path:
        train_chains, val_chains = split_tool_chains(tool_chains, args.train_val_split_ratio, shuffle=args.shuffle, seed=args.seed)
        convert_to_rl_data(train_chains, args.rl_output_train_path, exclude_envs=args.rl_exclude_envs)
        convert_to_rl_data(val_chains, args.rl_output_val_path, exclude_envs=args.rl_exclude_envs)

if __name__ == "__main__":
    main()
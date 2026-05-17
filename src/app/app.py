import json
import os
import time
import glob
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ---------- Configuration ----------
LOG_FILE_EXTENSION = ".json"
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# ---------- Log Directory Management ----------
def get_available_log_directories():
    """Scan current workspace for directories starting with 'log'."""
    log_dirs = []
    
    try:
        # List all items in the base directory
        for item in os.listdir(_BASE_DIR):
            item_path = os.path.join(_BASE_DIR, item)
            if os.path.isdir(item_path) and item.startswith('log'):
                log_dirs.append(item)
    except (OSError, FileNotFoundError) as e:
        print(f"Error scanning for log directories: {e}")
    
    return sorted(log_dirs)

def get_selected_log_folders(selected_dirs):
    """Get list of absolute paths for selected log directories."""
    folders = []
    
    if selected_dirs is None or 'All' in selected_dirs:
        # If None (no selection specified) or 'All' is selected, use all log directories
        available_dirs = get_available_log_directories()
        for dir_name in available_dirs:
            folder_path = os.path.join(_BASE_DIR, dir_name)
            if os.path.isdir(folder_path):
                folders.append(os.path.abspath(folder_path))
    else:
        # Use only selected directories (empty list means no directories)
        for dir_name in selected_dirs:
            folder_path = os.path.join(_BASE_DIR, dir_name)
            if os.path.isdir(folder_path):
                folders.append(os.path.abspath(folder_path))
    
    return folders

# ---------- Configuration ----------
DATA_FILE_EXTENSION = ".json"

# ---------- Caching for performance ----------
_conversation_indices_cache = None
_conversation_indices_cache_time = 0
_conversation_indices_file_mtime = 0
_conversation_line_cache = {}
_CACHE_TTL_SECONDS = 30
MAX_CONVERSATIONS = 100
_MAX_LINE_CACHE_SIZE = 1000
_scan_cache = None
_scan_cache_time = 0
_SCAN_CACHE_TTL_SECONDS = 10

# ---------- Data folder caching ----------
_data_scan_cache = None
_data_scan_cache_time = 0
_DATA_SCAN_CACHE_TTL_SECONDS = 10
_data_conversation_cache = {}
_MAX_DATA_CACHE_SIZE = 500


def _evict_line_cache_if_needed():
    """Prevent unbounded cache growth."""
    global _conversation_line_cache
    if len(_conversation_line_cache) > _MAX_LINE_CACHE_SIZE:
        sorted_items = sorted(_conversation_line_cache.items(), 
                            key=lambda x: x[1].get('_cache_time', 0))
        keep_count = int(_MAX_LINE_CACHE_SIZE * 0.8)
        _conversation_line_cache = dict(sorted_items[-keep_count:])

def scan_log_folders(force_refresh=False, selected_dirs=None):
    """Scan log folders for JSON files and return sorted list of file paths.
    
    Args:
        force_refresh: If True, ignore cache and reload from file
        selected_dirs: List of selected log directory names (None for all)
    """
    global _scan_cache, _scan_cache_time
    
    current_time = time.time()
    
    # Create cache key based on selected directories
    # None means all directories, [] means no directories
    if selected_dirs is None:
        cache_key = 'all'
    else:
        cache_key = tuple(sorted(selected_dirs))
    
    if not force_refresh and _scan_cache is not None and _scan_cache.get('_key') == cache_key:
        if current_time - _scan_cache_time < _SCAN_CACHE_TTL_SECONDS:
            # Check if any folder has been modified
            try:
                latest_mtime = 0
                for folder in get_selected_log_folders(selected_dirs):
                    if os.path.isdir(folder):
                        folder_mtime = os.path.getmtime(folder)
                        latest_mtime = max(latest_mtime, folder_mtime)
                
                # If no folder has been modified since cache was created, return cache
                if latest_mtime <= _scan_cache_time:
                    return _scan_cache['files']
            except (OSError, FileNotFoundError):
                pass
    
    log_folders = get_selected_log_folders(selected_dirs)
    json_files = []
    
    for folder in log_folders:
        if not os.path.isdir(folder):
            continue
            
        # Recursively scan for JSON files
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(LOG_FILE_EXTENSION):
                    file_path = os.path.join(root, file)
                    json_files.append(file_path)
    
    # Sort by modification time (newest first)
    json_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # Update cache
    _scan_cache = {'_key': cache_key, 'files': json_files}
    _scan_cache_time = current_time
    
    return json_files

def get_conversation_indices(force_refresh=False, max_conversations=None, selected_dirs=None):
    """Return list of conversation indices with their actual IDs.
    
    Args:
        force_refresh: If True, ignore cache and reload from file
        max_conversations: Maximum number of conversations to return (None for all)
        selected_dirs: List of selected log directory names (None for all)
    """
    global _conversation_indices_cache, _conversation_indices_cache_time, _conversation_indices_file_mtime
    
    current_time = time.time()
    
    # Create cache key based on selected directories
    # None means all directories, [] means no directories
    if selected_dirs is None:
        cache_key = 'all'
    else:
        cache_key = tuple(sorted(selected_dirs))
    
    if not force_refresh and _conversation_indices_cache is not None and _conversation_indices_cache.get('_key') == cache_key:
        if current_time - _conversation_indices_cache_time < _CACHE_TTL_SECONDS:
            # Check if any folder has been modified
            try:
                latest_mtime = 0
                for folder in get_selected_log_folders(selected_dirs):
                    if os.path.isdir(folder):
                        folder_mtime = os.path.getmtime(folder)
                        latest_mtime = max(latest_mtime, folder_mtime)
                
                if latest_mtime <= _conversation_indices_file_mtime:
                    cached_indices = _conversation_indices_cache.get('indices', [])
                    if max_conversations:
                        return cached_indices[:max_conversations]
                    return cached_indices
            except (OSError, FileNotFoundError):
                pass
    
    indices = []
    try:
        json_files = scan_log_folders(force_refresh=force_refresh, selected_dirs=selected_dirs)
        
        for file_idx, file_path in enumerate(json_files, 1):
            try:
                # Use filename without extension as conversation ID
                filename = os.path.basename(file_path)
                conv_id = os.path.splitext(filename)[0]  # Remove extension
                
                indices.append({
                    'id': conv_id,
                    'file_path': file_path,
                    'file_idx': file_idx
                })
                
                if max_conversations and len(indices) >= max_conversations:
                    break
                    
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
                # Still add it with a generic ID
                indices.append({
                    'id': f"conversation_{file_idx}",
                    'file_path': file_path,
                    'file_idx': file_idx
                })
                continue
        
        if not max_conversations or len(indices) < max_conversations:
            _conversation_indices_cache = {'_key': cache_key, 'indices': indices}
            _conversation_indices_cache_time = current_time
            try:
                # Store the latest folder modification time
                latest_mtime = 0
                for folder in get_selected_log_folders(selected_dirs):
                    if os.path.isdir(folder):
                        folder_mtime = os.path.getmtime(folder)
                        latest_mtime = max(latest_mtime, folder_mtime)
                _conversation_indices_file_mtime = latest_mtime
            except (OSError, FileNotFoundError):
                _conversation_indices_file_mtime = 0
            
    except Exception as e:
        print(f"Error scanning log folders: {e}")
        return []
    
    return indices

def _extract_message_content(msg_data, key):
    """Helper to extract content from message data."""
    if key not in msg_data:
        return ""
    
    content = msg_data[key]
    if isinstance(content, str):
        return content
    elif isinstance(content, list) and len(content) > 0:
        first_item = content[0]
        if isinstance(first_item, dict) and 'content' in first_item:
            return first_item['content']
        return str(first_item)
    return str(content)

def parse_conversation_data(conversation_data, file_idx=None, file_path=None):
    """Parse conversation data from JSON and return conversation data."""
    try:
        # Use filename without extension as conversation ID
        if file_path:
            filename = os.path.basename(file_path)
            conversation_id = os.path.splitext(filename)[0]
        else:
            conversation_id = conversation_data.get('id', f"conversation_{file_idx}")
        
        turns = {}
        agent_roles = set()
        turn_indices = set()
        
        # Handle different JSON structures
        if isinstance(conversation_data, dict):
            # Check if it's a direct conversation structure or wrapped
            if 'conversation' in conversation_data:
                conversation_data = conversation_data['conversation']
            
            for turn_idx, messages in conversation_data.items():
                if not turn_idx.isdigit():
                    continue
                turn_idx_int = int(turn_idx)
                turn_indices.add(turn_idx_int)
                items = []
                
                # Handle both list and dict formats for messages
                if isinstance(messages, list):
                    message_list = messages
                elif isinstance(messages, dict):
                    message_list = [messages]
                else:
                    continue
                
                for message in message_list:
                    if not isinstance(message, dict):
                        continue
                        
                    agent = message.get('agent', 'Unknown')
                    agent_roles.add(agent)
                    
                    if 'messages' in message:
                        input_data = output_data = system_data = reasoning_data = ""
                        
                        for msg in message['messages']:
                            if 'user' in msg:
                                input_data = _extract_message_content(msg, 'user')
                            elif 'assistant_think' in msg:
                                reasoning_data = _extract_message_content(msg, 'assistant_think')
                            elif 'assistant' in msg:
                                output_data = _extract_message_content(msg, 'assistant')
                            elif 'system' in msg:
                                system_data = _extract_message_content(msg, 'system')
                    else:
                        input_data = _extract_message_content(message, 'user')
                        reasoning_data = _extract_message_content(message, 'assistant_think')
                        output_data = _extract_message_content(message, 'assistant')
                        system_data = _extract_message_content(message, 'system')
                    
                    
                    item_data = {
                        'agent': agent,
                        'input': input_data,
                        'output': output_data,
                        'reasoning': reasoning_data,
                        'system': system_data,
                        'turn_idx': turn_idx_int,
                        'file_idx': file_idx,
                        'file_path': file_path,
                        'conversation_id': conversation_id
                    }
                    items.append(item_data)
                
                if items:  # Only add if we have valid items
                    turns[turn_idx_int] = items
        
        return {
            'conversation_id': conversation_id,
            'turns': turns,
            'agent_roles': sorted(list(agent_roles)),
            'turn_indices': sorted(list(turn_indices)),
            '_cache_time': time.time()
        }
    except Exception as e:
        print(f"Error parsing conversation data from {file_path}: {e}")
        # Return empty structure instead of raising exception
        return {
            'conversation_id': conversation_id if file_path else f"conversation_{file_idx}",
            'turns': {},
            'agent_roles': [],
            'turn_indices': [],
            '_cache_time': time.time()
        }

def load_conversation_by_file(file_path, file_idx=None, use_cache=True):
    """Load and parse a specific conversation from a JSON file."""
    global _conversation_line_cache
    
    cache_key = file_path  # Use file path as cache key
    
    if use_cache and cache_key in _conversation_line_cache:
        return _conversation_line_cache[cache_key]
    
    if not os.path.isfile(file_path):
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            conversation_data = json.load(f)
        
        parsed_data = parse_conversation_data(conversation_data, file_idx, file_path)
        
        if use_cache:
            _evict_line_cache_if_needed()
            _conversation_line_cache[cache_key] = parsed_data
            
        return parsed_data
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def load_log_data(max_conversations=None):
    """Load and parse log data from JSON files in log folders
    
    Args:
        max_conversations: Maximum number of conversations to load (None for all)
    """
    indices = get_conversation_indices(max_conversations=max_conversations)
    conversations = {}
    
    for idx in indices:
        conv_data = load_conversation_by_file(idx['file_path'], idx['file_idx'])
        if conv_data:
            conversations[conv_data['conversation_id']] = conv_data['turns']
    
    return conversations


def filter_trace_conversations(conversations, selected_conversation, selected_agent_role, selected_turn_idx):
    """Filter conversations based on selected criteria"""
    result = {}
    
    conversation_filtered = {}
    if selected_conversation != 'All':
        if selected_conversation in conversations:
            conversation_filtered[selected_conversation] = conversations[selected_conversation]
    else:
        conversation_filtered = conversations.copy()
    
    for conversation_id, turns in conversation_filtered.items():
        filtered_turns = {}
        
        for turn_idx, items in turns.items():
            if selected_turn_idx != 'All':
                try:
                    selected_turn_int = int(selected_turn_idx)
                    if turn_idx != selected_turn_int:
                        continue
                except (ValueError, TypeError):
                    continue
            
            filtered_items = []
            for item in items:
                if selected_agent_role != 'All' and item['agent'] != selected_agent_role:
                    continue
                
                filtered_items.append(item)
            
            if filtered_items:
                filtered_turns[turn_idx] = filtered_items
        
        if filtered_turns:
            result[conversation_id] = filtered_turns
    
    return result

# ---------- Data Folder Functions (Analysis Mode) ----------

def get_available_data_directories():
    """Scan current workspace for directories starting with 'data'."""
    data_dirs = []
    
    try:
        for item in os.listdir(_BASE_DIR):
            item_path = os.path.join(_BASE_DIR, item)
            if os.path.isdir(item_path) and item.startswith('data'):
                data_dirs.append(item)
    except (OSError, FileNotFoundError) as e:
        print(f"Error scanning for data directories: {e}")
    
    return sorted(data_dirs)

def get_selected_data_folders(selected_dirs):
    """Get list of absolute paths for selected data directories."""
    folders = []
    
    if selected_dirs is None or 'All' in selected_dirs:
        available_dirs = get_available_data_directories()
        for dir_name in available_dirs:
            folder_path = os.path.join(_BASE_DIR, dir_name)
            if os.path.isdir(folder_path):
                folders.append(os.path.abspath(folder_path))
    else:
        for dir_name in selected_dirs:
            folder_path = os.path.join(_BASE_DIR, dir_name)
            if os.path.isdir(folder_path):
                folders.append(os.path.abspath(folder_path))
    
    return folders

def scan_data_folders(force_refresh=False, selected_dirs=None):
    """Scan data folders for JSON files and return sorted list of file paths."""
    global _data_scan_cache, _data_scan_cache_time
    
    current_time = time.time()
    
    if selected_dirs is None:
        cache_key = 'all'
    else:
        cache_key = tuple(sorted(selected_dirs))
    
    if not force_refresh and _data_scan_cache is not None and _data_scan_cache.get('_key') == cache_key:
        if current_time - _data_scan_cache_time < _DATA_SCAN_CACHE_TTL_SECONDS:
            try:
                latest_mtime = 0
                for folder in get_selected_data_folders(selected_dirs):
                    if os.path.isdir(folder):
                        folder_mtime = os.path.getmtime(folder)
                        latest_mtime = max(latest_mtime, folder_mtime)
                
                if latest_mtime <= _data_scan_cache_time:
                    return _data_scan_cache['files']
            except (OSError, FileNotFoundError):
                pass
    
    data_folders = get_selected_data_folders(selected_dirs)
    json_files = []
    
    for folder in data_folders:
        if not os.path.isdir(folder):
            continue
            
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(DATA_FILE_EXTENSION):
                    file_path = os.path.join(root, file)
                    json_files.append(file_path)
    
    json_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    _data_scan_cache = {'_key': cache_key, 'files': json_files}
    _data_scan_cache_time = current_time
    
    return json_files

def get_data_conversation_indices(max_conversations=None, selected_dirs=None):
    """Return list of data file indices with their IDs."""
    indices = []
    try:
        json_files = scan_data_folders(force_refresh=False, selected_dirs=selected_dirs)
        
        for file_idx, file_path in enumerate(json_files, 1):
            try:
                filename = os.path.basename(file_path)
                conv_id = os.path.splitext(filename)[0]
                
                indices.append({
                    'id': conv_id,
                    'file_path': file_path,
                    'file_idx': file_idx
                })
                
                if max_conversations and len(indices) >= max_conversations:
                    break
                    
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
                indices.append({
                    'id': f"conversation_{file_idx}",
                    'file_path': file_path,
                    'file_idx': file_idx
                })
                continue
    
    except Exception as e:
        print(f"Error scanning data folders: {e}")
        return []
    
    return indices

def load_data_conversation(file_path, file_idx=None, use_cache=True):
    """Load and parse a specific data conversation from a JSON file."""
    global _data_conversation_cache
    
    cache_key = file_path
    
    if use_cache and cache_key in _data_conversation_cache:
        return _data_conversation_cache[cache_key]
    
    if not os.path.isfile(file_path):
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        parsed_data = parse_data_conversation(data, file_idx, file_path)
        
        if use_cache:
            if len(_data_conversation_cache) > _MAX_DATA_CACHE_SIZE:
                oldest_keys = list(_data_conversation_cache.keys())[:100]
                for k in oldest_keys:
                    del _data_conversation_cache[k]
            _data_conversation_cache[cache_key] = parsed_data
        
        return parsed_data
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def parse_data_conversation(data, file_idx=None, file_path=None):
    """Parse data conversation and return structured format."""
    conversation_id = ""
    try:
        if file_path:
            filename = os.path.basename(file_path)
            conversation_id = os.path.splitext(filename)[0]
        else:
            conversation_id = data.get('id', f"conversation_{file_idx}")
        
        nodes = data.get('nodes', [])
        turns = {}
        
        for node_idx, node in enumerate(nodes):
            node_turn_idx = node_idx + 1
            
            steps = node.get('steps', [])
            step_items = []
            
            for step in steps:
                role = step.get('role', 'unknown')
                content = step.get('content', '')
                
                step_item = {
                    'role': role,
                    'content': content,
                    'turn_idx': node_turn_idx,
                    'node_idx': node_idx,
                    'file_idx': file_idx,
                    'file_path': file_path,
                    'conversation_id': conversation_id
                }
                step_items.append(step_item)
            
            if step_items:
                turns[node_turn_idx] = step_items
        
        return {
            'conversation_id': conversation_id,
            'turns': turns,
            'total_nodes': len(nodes),
            'file_path': file_path,
            'file_idx': file_idx,
            'seed': data.get('seed', ''),
            'scenario': data.get('scenario', ''),
            '_cache_time': time.time()
        }
    
    except Exception as e:
        print(f"Error parsing data conversation from {file_path}: {e}")
        return {
            'conversation_id': conversation_id if conversation_id else f"conversation_{file_idx}",
            'turns': {},
            'total_nodes': 0,
            'file_path': file_path,
            'file_idx': file_idx,
            'seed': '',
            'scenario': '',
            '_cache_time': time.time()
        }

def calculate_analysis_metrics(conversation_indices):
    """Calculate analysis metrics from loaded conversations.
    
    Counts:
    - A complete tool_call + tool_response = 1 tool call
    - A complete user + assistant = 1 user interaction
    - Number of turns = tool calls + user interactions
    """
    metrics = {
        'total_conversations': len(conversation_indices),
        'total_nodes': 0,
        'turns_per_conversation': [],
        'steps_per_conversation': [],
        'tool_calls_per_conversation': [],
        'user_interactions_per_conversation': [],
        'steps_per_turn': [],
        'tool_calls_per_turn': [],
        'user_interactions_per_turn': [],
    }
    
    total_nodes = 0
    
    def count_pairs(steps):
        """Count complete (role + next_role) pairs in steps.
        
        - tool_call followed by tool_response = 1 tool call
        - user followed by assistant = 1 user interaction
        """
        tool_calls = 0
        user_interactions = 0
        
        # Build list of roles in order
        roles = [s.get('role', '') for s in steps]
        
        # Count tool_call + tool_response pairs
        i = 0
        while i < len(roles) - 1:
            if roles[i] == 'tool_call' and roles[i + 1] == 'tool_response':
                tool_calls += 1
                i += 2  # Skip both
            else:
                i += 1
        
        # Count user + assistant pairs (user followed by assistant)
        i = 0
        while i < len(roles) - 1:
            if roles[i] == 'user' and roles[i + 1] == 'assistant':
                user_interactions += 1
                i += 2  # Skip both
            else:
                i += 1
        
        return tool_calls, user_interactions
    
    for conv_info in conversation_indices:
        conv_data = load_data_conversation(conv_info['file_path'], conv_info['file_idx'])
        if not conv_data:
            continue
        
        turns = conv_data.get('turns', {})
        num_nodes = conv_data.get('total_nodes', 0)
        
        total_nodes += num_nodes
        
        conv_total_steps = 0
        conv_total_tool_calls = 0
        conv_total_user_interactions = 0
        conv_total_turns = 0
        
        for turn_idx, steps in turns.items():
            num_steps = len(steps)
            
            # Count pairs: tool_call+tool_response and user+assistant
            tool_calls, user_interactions = count_pairs(steps)
            
            # Number of turns = tool calls + user interactions
            num_turns = tool_calls + user_interactions
            
            conv_total_steps += num_steps
            conv_total_tool_calls += tool_calls
            conv_total_user_interactions += user_interactions
            conv_total_turns += num_turns
            
            metrics['steps_per_turn'].append({
                'conversation_id': conv_data['conversation_id'],
                'turn_idx': turn_idx,
                'count': num_steps
            })
            metrics['tool_calls_per_turn'].append({
                'conversation_id': conv_data['conversation_id'],
                'turn_idx': turn_idx,
                'count': tool_calls
            })
            metrics['user_interactions_per_turn'].append({
                'conversation_id': conv_data['conversation_id'],
                'turn_idx': turn_idx,
                'count': user_interactions
            })
        
        metrics['total_nodes'] = total_nodes
        metrics['turns_per_conversation'].append({
            'conversation_id': conv_data['conversation_id'],
            'count': conv_total_turns
        })
        metrics['steps_per_conversation'].append({
            'conversation_id': conv_data['conversation_id'],
            'count': conv_total_steps
        })
        metrics['tool_calls_per_conversation'].append({
            'conversation_id': conv_data['conversation_id'],
            'count': conv_total_tool_calls
        })
        metrics['user_interactions_per_conversation'].append({
            'conversation_id': conv_data['conversation_id'],
            'count': conv_total_user_interactions
        })
    
    n = metrics['total_conversations']
    n_turns = len(metrics['turns_per_conversation'])
    n_steps_turns = len(metrics['steps_per_turn'])
    
    total_turns = sum(d['count'] for d in metrics['turns_per_conversation'])
    total_steps = sum(d['count'] for d in metrics['steps_per_conversation'])
    total_tool_calls = sum(d['count'] for d in metrics['tool_calls_per_conversation'])
    total_user_interactions = sum(d['count'] for d in metrics['user_interactions_per_conversation'])
    
    metrics['total_turns'] = total_turns
    metrics['total_steps'] = total_steps
    metrics['total_tool_calls'] = total_tool_calls
    metrics['total_user_interactions'] = total_user_interactions
    
    metrics['avg_turns_per_conversation'] = total_turns / n if n > 0 else 0
    metrics['avg_steps_per_conversation'] = total_steps / n if n > 0 else 0
    metrics['avg_tool_calls_per_conversation'] = total_tool_calls / n if n > 0 else 0
    metrics['avg_user_interactions_per_conversation'] = total_user_interactions / n if n > 0 else 0
    
    metrics['avg_steps_per_turn'] = sum(d['count'] for d in metrics['steps_per_turn']) / n_steps_turns if n_steps_turns > 0 else 0
    metrics['avg_tool_calls_per_turn'] = sum(d['count'] for d in metrics['tool_calls_per_turn']) / n_steps_turns if n_steps_turns > 0 else 0
    metrics['avg_user_interactions_per_turn'] = sum(d['count'] for d in metrics['user_interactions_per_turn']) / n_steps_turns if n_steps_turns > 0 else 0
    
    return metrics

# ---------- Analysis route ----------
@app.route('/analysis')
def analysis():
    """Main page for Analysis Mode."""
    selected_conversation = request.args.get('conversation', 'All')
    selected_turn = request.args.get('turn', 'All')
    selected_data_dirs = request.args.getlist('data_dirs')
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    
    available_data_dirs = get_available_data_directories()
    
    if selected_data_dirs and 'All' in selected_data_dirs:
        dirs_for_filter = None
    elif selected_data_dirs:
        dirs_for_filter = selected_data_dirs
    else:
        dirs_for_filter = []
    
    indices = get_data_conversation_indices(max_conversations=MAX_CONVERSATIONS, selected_dirs=dirs_for_filter)
    
    conversation_ids = [idx['id'] for idx in indices]
    
    if not conversation_ids:
        return render_template('template.html',
                             mode='analysis',
                             conversations=[],
                             turns=[],
                             selected_conversation=None,
                             selected_turn='All',
                             selected_data_dirs=selected_data_dirs,
                             available_data_dirs=available_data_dirs,
                             steps_data={},
                             analysis_data={})
    
    loaded_conversations = []
    all_turn_indices = set()
    
    for idx in indices:
        conv_data = load_data_conversation(idx['file_path'], idx['file_idx'])
        if conv_data:
            loaded_conversations.append({
                'id': conv_data['conversation_id'],
                'file_path': idx['file_path'],
                'file_idx': idx['file_idx']
            })
            all_turn_indices.update(conv_data['turns'].keys())
    
    turn_indices = sorted(list(all_turn_indices))
    
    if selected_conversation == 'All' or selected_conversation not in conversation_ids:
        selected_conversation = conversation_ids[0] if conversation_ids else None
    
    steps_data = {}
    if selected_conversation:
        for idx in indices:
            if idx['id'] == selected_conversation:
                conv_data = load_data_conversation(idx['file_path'], idx['file_idx'])
                if conv_data:
                    if selected_turn != 'All':
                        try:
                            turn_int = int(selected_turn)
                            if turn_int in conv_data['turns']:
                                steps_data = {turn_int: conv_data['turns'][turn_int]}
                        except (ValueError, TypeError):
                            pass
                    else:
                        steps_data = conv_data['turns']
                break
    
    analysis_data = calculate_analysis_metrics(indices)
    
    return render_template('template.html',
                         mode='analysis',
                         conversations=conversation_ids,
                         turns=turn_indices,
                         selected_conversation=selected_conversation,
                         selected_turn=selected_turn,
                         selected_data_dirs=selected_data_dirs,
                         available_data_dirs=available_data_dirs,
                         steps_data=steps_data,
                         analysis_data=analysis_data)

# ---------- Combined route ----------
@app.route('/')
def index():
    """Main page with filters for trace mode."""
    selected_conversation = request.args.get('conversation', 'All')
    selected_turn = request.args.get('turn', 'All')
    selected_agent_role = request.args.get('agent_role', 'All')
    selected_log_dirs = request.args.getlist('log_dirs')
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    
    # Get available log directories for the filter
    available_log_dirs = get_available_log_directories()
    
    # Update the get_log_folders function calls to use selected directories
    # We need to modify the caching functions to accept selected directories
    # For now, we'll use a simple approach by filtering the indices after getting them
    
    # Handle log directory selection:
    # - If 'All' is selected or nothing is selected, use all directories (None)
    # - Otherwise, pass the selected directories to filter
    if selected_log_dirs and 'All' in selected_log_dirs:
        # 'All' selected - use all directories
        dirs_for_filter = None
    elif selected_log_dirs:
        # Specific directories selected
        dirs_for_filter = selected_log_dirs
    else:
        # Empty selection - no directories selected, should show no conversations
        dirs_for_filter = []  # Empty list means no directories
    
    indices = get_conversation_indices(force_refresh=force_refresh, max_conversations=MAX_CONVERSATIONS, selected_dirs=dirs_for_filter)
    
    conversation_ids = [idx['id'] for idx in indices]
    
    if not conversation_ids:
        return render_template('template.html',
                             mode='trace',
                             conversations=[],
                             turns=[],
                             agent_roles=[],
                             selected_conversation=None,
                             selected_turn='All',
                             selected_agent_role='All',
                             selected_log_dirs=selected_log_dirs,
                             available_log_dirs=available_log_dirs,
                             trace_data={},
                             analysis_data=[])
    
    # Load conversations and collect metadata
    conversations = {}
    all_turn_indices = set()
    all_agent_roles = set()
    
    for idx in indices:
        conv_data = load_conversation_by_file(idx['file_path'], idx['file_idx'])
        if conv_data:
            conversations[conv_data['conversation_id']] = conv_data['turns']
            
            # Only collect turn indices from the selected conversation (or all if "All" selected)
            if selected_conversation == 'All' or conv_data['conversation_id'] == selected_conversation:
                all_turn_indices.update(conv_data['turn_indices'])
                all_agent_roles.update(conv_data['agent_roles'])
    
    turn_indices = sorted(list(all_turn_indices))
    agent_roles = sorted(list(all_agent_roles))
    
    # Determine which conversation to display
    if selected_conversation == 'All' or selected_conversation not in conversation_ids:
        selected_conversation = conversation_ids[0] if conversation_ids else None
    
    trace_data = filter_trace_conversations(
        conversations,
        selected_conversation,
        selected_agent_role,
        selected_turn
    )
    
    return render_template('template.html',
                         mode='trace',
                         conversations=conversation_ids,
                         turns=turn_indices,
                         agent_roles=agent_roles,
                         selected_conversation=selected_conversation,
                         selected_turn=selected_turn,
                         selected_agent_role=selected_agent_role,
                         selected_log_dirs=selected_log_dirs,
                         available_log_dirs=available_log_dirs,
                         trace_data=trace_data,
                         analysis_data=[])

# ---------- API endpoints ----------

@app.route('/api/v2/conversations')
def api_v2_conversations():
    """Efficient API endpoint to get conversation list with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    indices = get_conversation_indices(max_conversations=MAX_CONVERSATIONS)
    
    total = len(indices)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    paginated_indices = indices[start_idx:end_idx]
    
    return jsonify({
        'conversations': paginated_indices,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': (total + per_page - 1) // per_page
        }
    })

@app.route('/api/v2/conversation/<conversation_id>')
def api_v2_conversation(conversation_id):
    """Efficient API endpoint to get a single conversation by ID."""
    indices = get_conversation_indices(max_conversations=None)
    
    file_path = file_idx = None
    for idx in indices:
        if idx['id'] == conversation_id:
            file_path, file_idx = idx['file_path'], idx['file_idx']
            break
    
    if file_path is None:
        return jsonify({'error': 'Conversation not found'}), 404
    
    conv_data = load_conversation_by_file(file_path, file_idx)
    if conv_data is None:
        return jsonify({'error': 'Failed to load conversation'}), 500
    
    return jsonify(conv_data)

@app.route('/api/v2/conversation/<conversation_id>/turn/<int:turn_idx>')
def api_v2_conversation_turn(conversation_id, turn_idx):
    """Efficient API endpoint to get a specific turn from a conversation."""
    indices = get_conversation_indices(max_conversations=None)
    
    file_path = file_idx = None
    for idx in indices:
        if idx['id'] == conversation_id:
            file_path, file_idx = idx['file_path'], idx['file_idx']
            break
    
    if file_path is None:
        return jsonify({'error': 'Conversation not found'}), 404
    
    conv_data = load_conversation_by_file(file_path, file_idx)
    if conv_data is None:
        return jsonify({'error': 'Failed to load conversation'}), 500
    
    turns = conv_data.get('turns', {})
    if turn_idx not in turns:
        return jsonify({'error': f'Turn {turn_idx} not found'}), 404
    
    return jsonify({
        'conversation_id': conversation_id,
        'turn_idx': turn_idx,
        'items': turns[turn_idx],
        'agent_roles': conv_data.get('agent_roles', []),
        'turn_indices': conv_data.get('turn_indices', [])
    })

@app.route('/api/v2/data-directories')
def api_v2_data_directories():
    """API endpoint to get available data directories."""
    available_dirs = get_available_data_directories()
    return jsonify({
        'data_directories': available_dirs,
        'total': len(available_dirs)
    })

@app.route('/api/v2/data-conversations')
def api_v2_data_conversations():
    """API endpoint to get data conversation list with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    selected_data_dirs = request.args.getlist('data_dirs')
    
    if selected_data_dirs and 'All' in selected_data_dirs:
        dirs_for_filter = None
    elif selected_data_dirs:
        dirs_for_filter = selected_data_dirs
    else:
        dirs_for_filter = []
    
    indices = get_data_conversation_indices(max_conversations=MAX_CONVERSATIONS, selected_dirs=dirs_for_filter)
    
    total = len(indices)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    paginated_indices = indices[start_idx:end_idx]
    
    return jsonify({
        'conversations': paginated_indices,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': (total + per_page - 1) // per_page
        }
    })

@app.route('/api/v2/log-directories')
def api_v2_log_directories():
    """API endpoint to get available log directories."""
    available_dirs = get_available_log_directories()
    return jsonify({
        'log_directories': available_dirs,
        'total': len(available_dirs)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)

import json
import os
import time
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ---------- Configuration ----------
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
FILE_EXTENSION = ".json"
MAX_CONVERSATIONS = 100
_CACHE_TTL_SECONDS = 30
_SCAN_CACHE_TTL_SECONDS = 10
_MAX_CACHE_SIZE = 1000

# ---------- Unified Directory Manager ----------
class DirectoryManager:
    """Unified manager for log and data directories."""
    
    @staticmethod
    def scan_directories(prefix):
        """Scan for directories starting with prefix."""
        dirs = []
        try:
            for item in os.listdir(_BASE_DIR):
                item_path = os.path.join(_BASE_DIR, item)
                if os.path.isdir(item_path) and item.startswith(prefix):
                    dirs.append(item)
        except (OSError, FileNotFoundError) as e:
            print(f"Error scanning for {prefix} directories: {e}")
        return sorted(dirs)
    
    @staticmethod
    def get_selected_folders(prefix, selected_dirs):
        """Get absolute paths for selected directories."""
        folders = []
        if selected_dirs is None or 'All' in selected_dirs:
            available = DirectoryManager.scan_directories(prefix)
            for dir_name in available:
                folder_path = os.path.join(_BASE_DIR, dir_name)
                if os.path.isdir(folder_path):
                    folders.append(os.path.abspath(folder_path))
        else:
            for dir_name in selected_dirs:
                folder_path = os.path.join(_BASE_DIR, dir_name)
                if os.path.isdir(folder_path):
                    folders.append(os.path.abspath(folder_path))
        return folders

# ---------- Data Folder Functions ----------
# (Copied from app.py to ensure independence)

_data_scan_cache = None
_data_scan_cache_time = 0
_DATA_SCAN_CACHE_TTL_SECONDS = 10
_data_conversation_cache = {}
_MAX_DATA_CACHE_SIZE = 500

def get_available_data_directories():
    """Scan current workspace for directories starting with 'data'."""
    return DirectoryManager.scan_directories('data')

def get_selected_data_folders(selected_dirs):
    """Get list of absolute paths for selected data directories."""
    return DirectoryManager.get_selected_folders('data', selected_dirs)

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
                if file.endswith(FILE_EXTENSION):
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
        
        # Extract mcp_servers list from each node
        all_mcp_servers = []
        for node in nodes:
            node_servers = node.get('mcp_servers', [])
            if isinstance(node_servers, list):
                all_mcp_servers.extend(node_servers)
        
        return {
            'conversation_id': conversation_id,
            'turns': turns,
            'total_nodes': len(nodes),
            'file_path': file_path,
            'file_idx': file_idx,
            'seed': data.get('seed', ''),
            'scenario': data.get('scenario', ''),
            'mcp_servers': all_mcp_servers,
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

# ---------- Main Route ----------
@app.route('/')
def index():
    """Main page for Lite Data Viewer."""
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
        return render_template('viewer_template.html',
                             mode='viewer',
                             conversations=[],
                             turns=[],
                             selected_conversation=None,
                             selected_turn='All',
                             selected_data_dirs=selected_data_dirs,
                             available_data_dirs=available_data_dirs,
                             steps_data={})
    
    all_turn_indices = set()
    
    # Determine which conversation to display
    if selected_conversation == 'All' or selected_conversation not in conversation_ids:
        selected_conversation = conversation_ids[0] if conversation_ids else None
    
    steps_data = {}
    if selected_conversation:
        for idx in indices:
            if idx['id'] == selected_conversation:
                conv_data = load_data_conversation(idx['file_path'], idx['file_idx'])
                if conv_data:
                    all_turn_indices.update(conv_data['turns'].keys())
                    
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
    
    turn_indices = sorted(list(all_turn_indices))
    
    return render_template('viewer_template.html',
                         mode='viewer',
                         conversations=conversation_ids,
                         turns=turn_indices,
                         selected_conversation=selected_conversation,
                         selected_turn=selected_turn,
                         selected_data_dirs=selected_data_dirs,
                         available_data_dirs=available_data_dirs,
                         steps_data=steps_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)

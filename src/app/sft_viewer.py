import json
import os
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SFT_FILE = os.path.join(_BASE_DIR, 'mcp_factory_sft.json')

_sft_data_cache = None
_sft_cache_time = 0
_CACHE_TTL_SECONDS = 10


def load_sft_data(force_refresh=False):
    global _sft_data_cache, _sft_cache_time
    
    import time
    current_time = time.time()
    
    if not force_refresh and _sft_data_cache is not None:
        if current_time - _sft_cache_time < _CACHE_TTL_SECONDS:
            try:
                if os.path.isfile(_SFT_FILE):
                    file_mtime = os.path.getmtime(_SFT_FILE)
                    if file_mtime <= _sft_cache_time:
                        return _sft_data_cache
            except (OSError, FileNotFoundError):
                pass
    
    data = []
    try:
        with open(_SFT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        _sft_data_cache = data
        _sft_cache_time = current_time
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error reading SFT file: {e}")
        return []
    
    return data


def parse_history_item(item):
    if isinstance(item, str):
        return item
    if isinstance(item, list):
        return '\n'.join(str(x) for x in item)
    return str(item)

def parse_sft_item(item):
    result = {
        'instruction': item.get('instruction', ''),
        'input': item.get('input', ''),
        'output': item.get('output', ''),
        'system': item.get('system', ''),
        'history': item.get('history', [])
    }
    
    output = result['output']
    if '<think>' in output:
        parts = output.split('</think>', 1)
        if len(parts) >= 2:
            result['reasoning'] = parts[0].replace('<think>', '').strip()
            result['output'] = parts[1].strip()
        else:
            result['reasoning'] = ''
            result['output'] = output.strip()
    else:
        result['reasoning'] = ''
        result['output'] = output.strip()
    
    history = result['history']
    parsed_history = []
    if history and isinstance(history, list):
        for turn in history:
            if isinstance(turn, list) and len(turn) >= 2:
                parsed_history.append({
                    'input': parse_history_item(turn[0]),
                    'output': parse_history_item(turn[1])
                })
    result['history'] = parsed_history
    
    return result


@app.route('/')
def index():
    selected_idx = request.args.get('conversation', '0')
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    
    sft_data = load_sft_data(force_refresh=force_refresh)
    total = len(sft_data)
    
    # Get valid index
    try:
        idx = int(selected_idx)
    except (ValueError, TypeError):
        idx = 0
    
    # Clamp to valid range
    if idx < 0:
        idx = 0
    if total > 0 and idx >= total:
        idx = total - 1
    
    # Parse selected item
    parsed = parse_sft_item(sft_data[idx]) if total > 0 and 0 <= idx < total else None
    
    return render_template('sft_viewer_template.html',
                          total=total,
                          indices=list(range(total)),
                          selected_idx=idx,
                          sft_item=parsed)


@app.route('/api/v2/sft-conversations')
def api_v2_sft_conversations():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    sft_data = load_sft_data()
    total = len(sft_data)
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    return jsonify({
        'conversations': [{'id': str(i)} for i in range(start_idx, min(end_idx, total))],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': (total + per_page - 1) // per_page
        }
    })


@app.route('/api/v2/sft-conversation/<int:index>')
def api_v2_sft_conversation(index):
    sft_data = load_sft_data()
    
    if index < 0 or index >= len(sft_data):
        return jsonify({'error': 'Conversation not found'}), 404
    
    item = sft_data[index]
    parsed = parse_sft_item(item)
    
    return jsonify({
        'index': index,
        'instruction': parsed['instruction'],
        'input': parsed['input'],
        'output': parsed['output'],
        'reasoning': parsed['reasoning'],
        'system': parsed['system'],
        'history': parsed['history']
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)
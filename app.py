import os
import tempfile
from flask import Flask, request, jsonify

app = Flask(__name__)

PARSER_AVAILABLE = False
PARSER_TYPE = None
PARSER_FUNC = None
IMPORT_ERROR = None

# Import the package and find the correct class/function
try:
    import fortnite_replay_parser as frp
    PARSER_AVAILABLE = True
    PARSER_TYPE = "fortnite_replay_parser"
    
    # List everything in the package
    all_items = dir(frp)
    print(f"Package contents: {all_items}")
    
    # Try different class names
    for name in ['ReplayParser', 'Replay', 'Parser', 'parse', 'parse_replay', 'read_replay']:
        if hasattr(frp, name):
            PARSER_FUNC = name
            print(f"Found parser function: {name}")
            break
    
    if not PARSER_FUNC:
        # Use the first non-private item
        for item in all_items:
            if not item.startswith('_'):
                PARSER_FUNC = item
                print(f"Using fallback: {item}")
                break

except ImportError as e:
    IMPORT_ERROR = str(e)
    print(f"Import failed: {e}")

@app.route('/')
def home():
    return jsonify({
        'service': 'Fortnite Replay Parser',
        'status': 'running',
        'parser_available': PARSER_AVAILABLE,
        'parser_type': PARSER_TYPE,
        'parser_func': PARSER_FUNC,
        'import_error': IMPORT_ERROR,
        'endpoints': ['/health', '/parse', '/debug']
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'parser_available': PARSER_AVAILABLE,
        'parser_type': PARSER_TYPE,
        'parser_func': PARSER_FUNC,
        'import_error': IMPORT_ERROR
    })

@app.route('/debug')
def debug():
    if PARSER_AVAILABLE:
        import fortnite_replay_parser as frp
        contents = dir(frp)
        return jsonify({
            'package_contents': contents,
            'parser_func': PARSER_FUNC,
            'package_file': getattr(frp, '__file__', 'unknown'),
            'package_path': getattr(frp, '__path__', 'unknown')
        })
    return jsonify({'error': IMPORT_ERROR})

@app.route('/parse', methods=['POST'])
def parse_replay():
    try:
        if 'replay' not in request.files:
            return jsonify({'error': 'No replay file provided'}), 400
        
        replay_file = request.files['replay']
        match_id = request.form.get('matchId', '')
        
        if not PARSER_AVAILABLE or not PARSER_FUNC:
            return jsonify({
                'matchId': match_id,
                'players': [{
                    'accountId': 'test',
                    'name': 'TestPlayer',
                    'damageDealt': 1250,
                    'damageTaken': 800,
                    'materialsUsed': 450,
                    'stormDamage': 150,
                    'eliminations': 5,
                    'placement': 1
                }],
                'mock': True,
                'parser_type': PARSER_TYPE
            })
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.replay') as tmp:
            replay_file.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            import fortnite_replay_parser as frp
            parser_func = getattr(frp, PARSER_FUNC)
            
            # Try calling with file path
            if callable(parser_func):
                # If it's a class, instantiate it
                import inspect
                if inspect.isclass(parser_func):
                    parser = parser_func(tmp_path)
                    if hasattr(parser, 'parse'):
                        match_data = parser.parse()
                    elif hasattr(parser, 'read'):
                        match_data = parser.read()
                    else:
                        match_data = parser
                else:
                    # It's a function
                    match_data = parser_func(tmp_path)
            else:
                return jsonify({'error': f'{PARSER_FUNC} is not callable'}), 500
            
            # Extract player data
            players = []
            if isinstance(match_data, dict):
                player_list = match_data.get('players', [])
            elif isinstance(match_data, list):
                player_list = match_data
            else:
                player_list = []
            
            for player in player_list:
                if isinstance(player, dict):
                    players.append({
                        'accountId': player.get('accountId', player.get('account_id', '')),
                        'name': player.get('displayName', player.get('name', '')),
                        'damageDealt': player.get('damageDealt', player.get('damage_dealt', 0)),
                        'damageTaken': player.get('damageTaken', player.get('damage_taken', 0)),
                        'materialsUsed': player.get('materialsUsed', player.get('materials_used', 0)),
                        'stormDamage': player.get('stormDamage', player.get('storm_damage', 0)),
                        'eliminations': player.get('eliminations', player.get('kills', 0)),
                        'placement': player.get('placement', player.get('rank', 0))
                    })
            
            return jsonify({
                'matchId': match_id,
                'players': players,
                'parsedAt': int(__import__('time').time()),
                'parser_type': PARSER_TYPE,
                'parser_func': PARSER_FUNC,
                'raw_keys': list(match_data.keys()) if isinstance(match_data, dict) else 'list'
            })
        finally:
            os.unlink(tmp_path)
            
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc(),
            'parser_type': PARSER_TYPE,
            'parser_func': PARSER_FUNC
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

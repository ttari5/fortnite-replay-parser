import os
import traceback
import tempfile
from flask import Flask, request, jsonify

app = Flask(__name__)

PARSER_AVAILABLE = False
PARSER_TYPE = None
IMPORT_ERROR = None

# Try different import names
try:
    from fortnite_replay_parser import ReplayParser
    PARSER_AVAILABLE = True
    PARSER_TYPE = "fortnite_replay_parser"
    print("Loaded: fortnite_replay_parser")
except ImportError as e:
    IMPORT_ERROR = str(e)
    print(f"Import failed for fortnite_replay_parser: {e}")
    
    # Try alternative names
    try:
        import fortnite_replay_parser as frp
        PARSER_AVAILABLE = True
        PARSER_TYPE = "fortnite_replay_parser_alt"
        print("Loaded: fortnite_replay_parser (alt)")
    except ImportError as e2:
        print(f"Alt import failed: {e2}")

@app.route('/')
def home():
    return jsonify({
        'service': 'Fortnite Replay Parser',
        'status': 'running',
        'parser_available': PARSER_AVAILABLE,
        'parser_type': PARSER_TYPE,
        'import_error': IMPORT_ERROR,
        'endpoints': ['/health', '/parse', '/debug']
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'parser_available': PARSER_AVAILABLE,
        'parser_type': PARSER_TYPE,
        'import_error': IMPORT_ERROR
    })

@app.route('/debug')
def debug():
    import pkgutil
    modules = [m.name for m in pkgutil.iter_modules() if 'fortnite' in m.name.lower() or 'replay' in m.name.lower()]
    return jsonify({
        'fortnite_replay_parser': PARSER_AVAILABLE,
        'import_error': IMPORT_ERROR,
        'related_modules': modules
    })

@app.route('/parse', methods=['POST'])
def parse_replay():
    try:
        if 'replay' not in request.files:
            return jsonify({'error': 'No replay file provided'}), 400
        
        replay_file = request.files['replay']
        match_id = request.form.get('matchId', '')
        
        if not PARSER_AVAILABLE:
            # Return mock data for testing
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
        
        # Real parsing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.replay') as tmp:
            replay_file.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            parser = ReplayParser(tmp_path)
            match_data = parser.parse()
            
            players = []
            for player in match_data.get('players', []):
                players.append({
                    'accountId': player.get('accountId', ''),
                    'name': player.get('displayName', ''),
                    'damageDealt': player.get('damageDealt', 0),
                    'damageTaken': player.get('damageTaken', 0),
                    'materialsUsed': player.get('materialsUsed', 0),
                    'stormDamage': player.get('stormDamage', 0),
                    'eliminations': player.get('eliminations', 0),
                    'placement': player.get('placement', 0)
                })
            
            return jsonify({
                'matchId': match_id,
                'players': players,
                'parsedAt': int(__import__('time').time()),
                'parser_type': PARSER_TYPE
            })
        finally:
            os.unlink(tmp_path)
            
    except Exception as e:
        return jsonify({'error': str(e), 'parser_type': PARSER_TYPE}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

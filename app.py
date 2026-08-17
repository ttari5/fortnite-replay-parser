from flask import Flask, request, jsonify
import os
import tempfile

app = Flask(__name__)

# Try to import the parser
try:
    from fortnite_replay_parser import ReplayParser
    PARSER_AVAILABLE = True
except ImportError:
    PARSER_AVAILABLE = False
    print("Warning: fortnite-replay-parser not installed")

# Root route - so you don't get 404 at /
@app.route('/')
def home():
    return jsonify({
        'service': 'Fortnite Replay Parser',
        'status': 'running',
        'endpoints': ['/health', '/parse'],
        'parser_available': PARSER_AVAILABLE
    })

# Health check
@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'parser_available': PARSER_AVAILABLE
    })

# Parse replay file
@app.route('/parse', methods=['POST'])
def parse_replay():
    try:
        if 'replay' not in request.files:
            return jsonify({'error': 'No replay file provided'}), 400
        
        replay_file = request.files['replay']
        match_id = request.form.get('matchId', '')
        
        # If parser not available, return mock data
        if not PARSER_AVAILABLE:
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
                'mock': True
            })
        
        # Save to temp file
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
                'parsedAt': int(__import__('time').time())
            })
        finally:
            os.unlink(tmp_path)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

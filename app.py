import os
import tempfile
from flask import Flask, request, jsonify

app = Flask(__name__)

PARSER_AVAILABLE = False
PARSER_INFO = "not loaded"

try:
    import fortnite_replay_parser as frp
    PARSER_AVAILABLE = True
    PARSER_INFO = str(dir(frp))
except Exception as e:
    PARSER_INFO = str(e)

@app.route('/')
def home():
    return jsonify({
        'service': 'Fortnite Replay Parser',
        'parser_available': PARSER_AVAILABLE,
        'parser_info': PARSER_INFO
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'parser_available': PARSER_AVAILABLE,
        'parser_info': PARSER_INFO
    })

@app.route('/debug')
def debug():
    try:
        import fortnite_replay_parser as frp
        return jsonify({
            'dir': dir(frp),
            'file': str(getattr(frp, '__file__', 'none')),
            'path': str(getattr(frp, '__path__', 'none'))
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/parse', methods=['POST'])
def parse_replay():
    try:
        if 'replay' not in request.files:
            return jsonify({'error': 'No replay file provided'}), 400
        
        replay_file = request.files['replay']
        match_id = request.form.get('matchId', '')
        
        # Mock data for now
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
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

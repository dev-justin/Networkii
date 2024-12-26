from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from config import config, CONFIG_FILE
import socket
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('settings.html', config=config)

@app.route('/api/settings', methods=['GET'])
def get_settings():
    return jsonify(config.config)

@app.route('/api/settings', methods=['POST'])
def update_settings():
    try:
        # Check if config file is writable
        if os.path.exists(CONFIG_FILE):
            if not os.access(CONFIG_FILE, os.W_OK):
                return jsonify({'error': 'Config file is not writable'}), 500
        else:
            if not os.access(os.path.dirname(CONFIG_FILE) or '.', os.W_OK):
                return jsonify({'error': 'Directory is not writable'}), 500
        
        updates = request.json
        print(f"Received updates: {updates}")
        
        if not updates:
            return jsonify({'error': 'No data received'}), 400
        
        # Validate and convert numeric values
        converted_updates = {}  # Create a new dict for converted values
        for key, value in updates.items():
            if key in config.config:
                if isinstance(config.config[key], (int, float)):
                    try:
                        converted_updates[key] = type(config.config[key])(value)
                        print(f"Converted {key}: {value} to {converted_updates[key]}")
                    except ValueError:
                        print(f"Invalid value for {key}: {value}")
                        return jsonify({'error': f'Invalid value for {key}'}), 400
                else:
                    converted_updates[key] = value  # Keep non-numeric values as is
            else:
                print(f"Unknown key: {key}")
                return jsonify({'error': f'Unknown key: {key}'}), 400
        
        # Update config with converted values
        try:
            config.update(converted_updates)
            print(f"Updated config: {config.config}")
        except Exception as e:
            print(f"Failed to update config: {e}")
            return jsonify({'error': f'Failed to update config: {e}'}), 500
        
        # Always return a response
        return jsonify({
            'status': 'success',
            'message': 'Settings updated successfully',
            'config': config.config
        })
        
    except Exception as e:
        print(f"Error in update_settings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test_ping_target', methods=['POST'])
def test_ping_target():
    target = request.json.get('target')
    try:
        socket.gethostbyname(target)
        return jsonify({'status': 'success'})
    except socket.error:
        return jsonify({'error': 'Invalid host'}), 400

if __name__ == '__main__':
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Web interface available at: http://{local_ip}:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)  # Added debug=True for better error reporting 
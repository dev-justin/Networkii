from flask import Flask, jsonify, request, render_template_string
import logging
import threading
import ssl
import os
from ..utils.config_manager import config_manager

logger = logging.getLogger('config_server')

HTML_TEMPLATE = """
<html>
<head>
    <title>Networkii Configuration</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .warning {
            background: #fff3cd;
            color: #856404;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 20px;
            border: 1px solid #ffeeba;
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            color: #666;
        }
        input {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        button {
            background: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background: #45a049;
        }
        #status {
            margin-top: 20px;
            padding: 10px;
            border-radius: 4px;
            display: none;
        }
        .success {
            background: #dff0d8;
            color: #3c763d;
            border: 1px solid #d6e9c6;
        }
        .error {
            background: #f2dede;
            color: #a94442;
            border: 1px solid #ebccd1;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="warning">
            Note: This site uses a self-signed certificate for security.
            You may need to accept the security warning in your browser.
        </div>
        <h1>Networkii Configuration</h1>
        <form id="config-form">
            <div class="form-group">
                <label for="ping_target">Ping Target</label>
                <input type="text" id="ping_target" name="ping_target" placeholder="e.g. 1.1.1.1" required>
            </div>
            <div class="form-group">
                <label for="speed_test_interval">Speed Test Interval (minutes)</label>
                <input type="number" id="speed_test_interval" name="speed_test_interval" min="5" max="1440" required>
            </div>
            <button type="submit">Save Configuration</button>
        </form>
        <div id="status"></div>
    </div>
    
    <script>
        // Load current configuration
        fetch('/config')
            .then(response => response.json())
            .then(config => {
                document.getElementById('ping_target').value = config.ping_target;
                document.getElementById('speed_test_interval').value = config.speed_test_interval;
            })
            .catch(error => {
                console.error('Error loading configuration:', error);
            });
        
        // Handle form submission
        document.getElementById('config-form').onsubmit = async (e) => {
            e.preventDefault();
            const form = e.target;
            const status = document.getElementById('status');
            
            const config = {
                ping_target: form.ping_target.value,
                speed_test_interval: parseInt(form.speed_test_interval.value, 10)
            };
            
            try {
                const response = await fetch('/config', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(config)
                });
                
                const result = await response.json();
                status.textContent = result.message;
                status.className = result.success ? 'success' : 'error';
                status.style.display = 'block';
                
                if (result.success) {
                    setTimeout(() => {
                        status.style.display = 'none';
                    }, 3000);
                }
            } catch (error) {
                status.textContent = 'Error saving configuration. Please try again.';
                status.className = 'error';
                status.style.display = 'block';
            }
        };
    </script>
</body>
</html>
"""

class ConfigServer:
    def __init__(self, port=8080):
        self.port = port
        self.app = Flask(__name__)
        self.server_thread = None
        self.cert_file = os.path.expanduser('~/.config/networkii/cert.pem')
        self.key_file = os.path.expanduser('~/.config/networkii/key.pem')
        
        # Verify certificates exist
        if not os.path.exists(self.cert_file) or not os.path.exists(self.key_file):
            logger.error("SSL certificates not found. Please run the installation script to generate them.")
            raise FileNotFoundError("SSL certificates not found")
        
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template_string(HTML_TEMPLATE)
        
        @self.app.route('/config', methods=['GET'])
        def get_config():
            return jsonify(config_manager.get_config())
        
        @self.app.route('/config', methods=['POST'])
        def update_config():
            try:
                new_config = request.get_json()
                logger.info(f"Updating configuration: {new_config}")
                config_manager.update_config(new_config)
                return jsonify({
                    'success': True,
                    'message': 'Configuration updated successfully'
                })
            except Exception as e:
                logger.error(f"Error updating configuration: {e}")
                return jsonify({
                    'success': False,
                    'message': f'Error updating configuration: {str(e)}'
                }), 400
    
    def start(self):
        """Start the Flask server in a background thread"""
        def run_server():
            try:
                logger.info(f"Starting HTTPS configuration server on port {self.port}")
                
                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                ssl_context.load_cert_chain(self.cert_file, self.key_file)
                
                self.app.run(
                    host='0.0.0.0',
                    port=self.port,
                    ssl_context=ssl_context,
                    threaded=True
                )
            except Exception as e:
                logger.error(f"Error starting HTTPS server: {e}", exc_info=True)
                raise

        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
    
    def stop(self):
        """Stop the Flask server"""
        logger.info("Stopping configuration server")
        logger.info("Configuration server stopped") 
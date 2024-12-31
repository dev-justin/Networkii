from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
import threading
from ..utils.config_manager import config_manager

logger = logging.getLogger('config_server')

class ConfigHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        logger.debug(f"Received GET request for path: {self.path}")
        
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
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
                    <h1>Networkii Configuration</h1>
                    <form id="config-form">
                        <div class="form-group">
                            <label for="ping_target">Ping Target</label>
                            <input type="text" id="ping_target" name="ping_target" placeholder="e.g. 1.1.1.1" required>
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
                            ping_target: form.ping_target.value
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
            self.wfile.write(html.encode())
            
        elif self.path == '/config':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            config = config_manager.get_config()
            self.wfile.write(json.dumps(config).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/config':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                new_config = json.loads(post_data)
                
                logger.info(f"Updating configuration: {new_config}")
                config_manager.update_config(new_config)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    'success': True,
                    'message': 'Configuration updated successfully'
                }
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                logger.error(f"Error updating configuration: {e}")
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    'success': False,
                    'message': f'Error updating configuration: {str(e)}'
                }
                self.wfile.write(json.dumps(response).encode())

class ConfigServer:
    def __init__(self, port=8080):
        self.port = port
        self.server = None
        self.server_thread = None
    
    def start(self):
        """Start the configuration web server in a background thread"""
        def run_server():
            logger.info(f"Starting configuration server on port {self.port}")
            self.server = HTTPServer(('0.0.0.0', self.port), ConfigHandler)
            self.server.serve_forever()
        
        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
    
    def stop(self):
        """Stop the configuration web server"""
        if self.server:
            logger.info("Stopping configuration server")
            self.server.shutdown()
            self.server.server_close()
            self.server_thread.join()
            logger.info("Configuration server stopped") 
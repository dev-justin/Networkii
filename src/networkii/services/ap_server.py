from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import json
import logging
import os
import subprocess
import time

# Get logger for this module
logger = logging.getLogger('ap_server')

class APConfigHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        logger.debug(f"Received GET request for path: {self.path}")
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <html>
            <head>
                <title>Networkii Setup</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link rel="stylesheet" href="/styles.css">
            </head>
            <body>
                <div class="container">
                    <div class="image-section">
                        <div class="logo">NETWORKII</div>
                    </div>
                    <div class="form-section">
                        <h1>Welcome to Networkii</h1>
                        <p class="subtitle">Connect your device to a WiFi network to begin monitoring.</p>
                        <form id="wifi-form">
                            <div class="form-group">
                                <label for="ssid">Network Name</label>
                                <input type="text" id="ssid" name="ssid" placeholder="Enter WiFi name" required>
                            </div>
                            <div class="form-group">
                                <label for="password">Password</label>
                                <input type="password" id="password" name="password" placeholder="Enter WiFi password" required>
                            </div>
                            <button type="submit">Connect to Network</button>
                        </form>
                        <div id="status"></div>
                    </div>
                </div>
                <script>
                    document.getElementById('wifi-form').onsubmit = async (e) => {
                        e.preventDefault();
                        const form = e.target;
                        const status = document.getElementById('status');
                        
                        // Show status with loading
                        status.textContent = 'Connecting...';
                        status.className = 'show';
                        
                        const formData = new URLSearchParams();
                        formData.append('ssid', form.ssid.value);
                        formData.append('password', form.password.value);
                        
                        try {
                            const response = await fetch('/configure', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/x-www-form-urlencoded',
                                },
                                body: formData.toString()
                            });
                            const result = await response.json();
                            status.textContent = result.message;
                            status.classList.add(result.success ? 'success' : 'error');
                        } catch (error) {
                            status.textContent = 'Connection failed. Please try again.';
                            status.classList.add('error');
                        }
                    };
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        elif self.path == '/styles.css':
            try:
                with open('assets/styles.css', 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/css')
                    self.end_headers()
                    self.wfile.write(f.read())
            except Exception as e:
                logger.error(f"Error serving CSS file: {e}")
                self.send_error(404)
        elif self.path == '/ap_background.jpg':
            try:
                with open('assets/ap_background.jpg', 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'image/jpeg')
                    self.end_headers()
                    self.wfile.write(f.read())
            except Exception as e:
                logger.error(f"Error serving background image: {e}")
                self.send_error(404)
    
    def do_POST(self):
        logger.debug(f"Received POST request for path: {self.path}")
        if self.path == '/configure':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                logger.debug(f"Raw POST data: {post_data}")
                
                # Parse URL-encoded form data
                params = parse_qs(post_data)
                logger.debug(f"Parsed params: {params}")
                
                ssid = params.get('ssid', [''])[0]
                password = params.get('password', [''])[0]
                
                logger.debug(f"Attempting to configure WiFi with SSID: {ssid}")
                
                if not ssid:
                    logger.error("No SSID provided")
                    self._send_error_response("No SSID provided")
                    return
                
                logger.info("Configuring WiFi network...")
                success = self.server.network_manager.configure_wifi(ssid, password)
                logger.info(f"WiFi configuration {'successful' if success else 'failed'}")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    'success': success,
                    'message': 'Connected successfully!' if success else 'Connection failed. Please try again.'
                }
                self.wfile.write(json.dumps(response).encode())
                
                # If connection was successful and we have a callback, call it
                if success and self.server.on_wifi_configured:
                    logger.debug("Calling transition callback")
                    self.server.on_wifi_configured()
                
            except Exception as e:
                logger.error(f"Error processing POST request: {str(e)}")
                self._send_error_response(f"Internal error: {str(e)}")
    
    def _send_error_response(self, message):
        self.send_response(400)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {
            'success': False,
            'message': message
        }
        self.wfile.write(json.dumps(response).encode())

class APServer:
    def __init__(self, network_manager, on_wifi_configured=None, port=80):
        self.port = port
        self.network_manager = network_manager
        self.server = None
        self.on_wifi_configured = on_wifi_configured
    
    def _force_clear_port(self):
        """Force kill any process using port 80"""
        try:
            # Find process using port 80
            cmd = "lsof -i :80 | grep LISTEN | awk '{print $2}'"
            process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            pid = process.stdout.strip()
            
            if pid:
                logger.debug(f"Found process {pid} using port 80, killing it")
                # Kill the process
                subprocess.run(f"kill -9 {pid}", shell=True)
                logger.debug("Process killed successfully")
        except Exception as e:
            logger.error(f"Error while trying to clear port 80: {e}")
    
    def start(self):
        try:
            logger.info("Starting AP web server")
            
            # Force clear port 80 if it's in use
            self._force_clear_port()
            
            # Small delay to ensure port is released
            time.sleep(1)
            
            self.server = HTTPServer(('10.42.0.1', self.port), APConfigHandler)
            self.server.network_manager = self.network_manager
            self.server.on_wifi_configured = self.on_wifi_configured
            logger.debug(f"AP web server started on http://10.42.0.1:{self.port}")
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"Failed to start AP web server: {str(e)}")
            raise
    
    def shutdown(self):
        if self.server:
            logger.info("Shutting down AP web server...")
            try:
                self.server.shutdown()
                self.server.server_close()
                logger.info("AP web server shutdown complete")
            except Exception as e:
                logger.error(f"Error during server shutdown: {e}") 
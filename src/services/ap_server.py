from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import json
import logging

# Get logger for this module
logger = logging.getLogger('ap_server')

class APConfigHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        logger.info(f"Received GET request for path: {self.path}")
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <html>
            <head>
                <title>Networkii Setup</title>
                <style>
                    body { font-family: Arial; max-width: 500px; margin: 40px auto; padding: 20px; }
                    input, button { width: 100%; padding: 10px; margin: 10px 0; }
                    button { background: #4CAF50; color: white; border: none; cursor: pointer; }
                </style>
            </head>
            <body>
                <h1>Networkii WiFi Setup</h1>
                <form id="wifi-form">
                    <input type="text" name="ssid" placeholder="WiFi Name (SSID)" required>
                    <input type="password" name="password" placeholder="WiFi Password" required>
                    <button type="submit">Connect</button>
                </form>
                <div id="status"></div>
                <script>
                    document.getElementById('wifi-form').onsubmit = async (e) => {
                        e.preventDefault();
                        const form = e.target;
                        const formData = new URLSearchParams();
                        formData.append('ssid', form.ssid.value);
                        formData.append('password', form.password.value);
                        
                        const response = await fetch('/configure', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/x-www-form-urlencoded',
                            },
                            body: formData.toString()
                        });
                        const result = await response.json();
                        document.getElementById('status').textContent = result.message;
                    };
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
    
    def do_POST(self):
        logger.info(f"Received POST request for path: {self.path}")
        if self.path == '/configure':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                logger.info(f"Raw POST data: {post_data}")
                
                # Parse URL-encoded form data
                params = parse_qs(post_data)
                logger.info(f"Parsed params: {params}")
                
                ssid = params.get('ssid', [''])[0]
                password = params.get('password', [''])[0]
                
                logger.info(f"Extracted SSID: {ssid}, password length: {len(password)}")
                
                if not ssid:
                    logger.error("No SSID provided")
                    self._send_error_response("No SSID provided")
                    return
                
                logger.info(f"Attempting to configure WiFi with SSID: {ssid}")
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
                    logger.info("Calling transition callback")
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
    
    def start(self):
        try:
            logger.info("Starting AP web server...")
            self.server = HTTPServer(('10.42.0.1', self.port), APConfigHandler)
            self.server.network_manager = self.network_manager
            self.server.on_wifi_configured = self.on_wifi_configured
            logger.info(f"AP web server started successfully on http://10.42.0.1:{self.port}")
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"Failed to start AP web server: {str(e)}")
            raise
    
    def shutdown(self):
        if self.server:
            logger.info("Shutting down AP web server...")
            self.server.shutdown()
            self.server.server_close()
            logger.info("AP web server shutdown complete") 
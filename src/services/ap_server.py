from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import json

class APConfigHandler(BaseHTTPRequestHandler):
    def do_GET(self):
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
                        const response = await fetch('/configure', {
                            method: 'POST',
                            body: new FormData(form)
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
        if self.path == '/configure':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(post_data)
            
            ssid = params.get('ssid', [''])[0]
            password = params.get('password', [''])[0]
            
            success = self.server.network_manager.configure_wifi(ssid, password)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'success': success,
                'message': 'Connected successfully!' if success else 'Connection failed. Please try again.'
            }
            self.wfile.write(json.dumps(response).encode())

class APServer:
    def __init__(self, network_manager, port=80):
        self.port = port
        self.server = HTTPServer(('192.168.4.1', port), APConfigHandler)
        self.server.network_manager = network_manager
    
    def start(self):
        self.server.serve_forever() 
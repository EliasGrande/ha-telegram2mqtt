from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import json
import os

OUTPUT_FILE = os.environ.get('TELEGRAM_MOCK_OUTPUT', '/tmp/telegram_messages.jsonl')


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/health':
            body = json.dumps({'ok': True}).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        payload = {
            'path': parsed.path,
            'query': parse_qs(parsed.query),
        }
        text_values = payload['query'].get('text', [])
        if text_values:
            print(f"Telegram mock received message: {text_values[0]}", flush=True)
        else:
            print(f"Telegram mock received request: {parsed.path}", flush=True)
        with open(OUTPUT_FILE, 'a', encoding='utf-8') as file:
            file.write(json.dumps(payload, ensure_ascii=False) + '\n')

        body = json.dumps({'ok': True}).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


if __name__ == '__main__':
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    server = HTTPServer(('0.0.0.0', 8081), Handler)
    server.serve_forever()

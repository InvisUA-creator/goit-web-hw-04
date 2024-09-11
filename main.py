from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import pathlib
import socket
import threading
import json
from datetime import datetime 

UDP_IP = '127.0.0.1'
UDP_PORT = 5000


DATA_FILE = 'storage/data.json'


def save_to_json(data):
    pathlib.Path('storage').mkdir(exist_ok=True)
    try:
        with open(DATA_FILE, 'r') as f:
            existing_data = json.load(f)
    except (FileNotFoundError):
        existing_data = {}
    except json.JSONDecodeError:
        existing_data = {}

    existing_data.update(data)

    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(existing_data, f, indent=2)
            print(f'Data saved to {DATA_FILE}')
    except Exception as e:
        print(f'Error saving data: {e}')



class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message.html':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_staic()
            else:
                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        try:
            self.send_response(status)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open(filename, 'rb') as fd:
                self.wfile.write(fd.read())
        except FileNotFoundError:
            self.send_html_file('error.html', 404)

    def send_staic(self):
        try:
            file_path = pathlib.Path().joinpath(self.path[1:])
            with open(file_path, 'rb') as file:
                self.send_response(200)
                if self.path.endswith('.png'):
                    self.send_header('Content-type', 'image/png')
                elif self.path.endswith('.css'):
                    self.send_header('Content-type', 'text/css')
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_html_file('error.html', 404)


    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        print(data)
        data_parse = urllib.parse.unquote_plus(data.decode())
        print(data_parse)
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        print(data_dict)
        udp_client_send(data_dict)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()


def udp_client_send(data):
    try:
        serialized_data = json.dumps(data).encode('utf-8')
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(serialized_data, (UDP_IP, UDP_PORT))
        client_socket.close()
        print('Data sent to SOCKET server')
    except Exception as e:
        print(f'Error sending data to Socket server: {e}')



def udp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((UDP_IP, UDP_PORT))
    print(f'UDP server started on {UDP_IP}:{UDP_PORT}')

    while True:
        try:
            message, address = server_socket.recvfrom(1024)
            data = json.loads(message.decode('utf-8'))
            print(f'Received data from {address}: {data}')
            timestamp = datetime.now().isoformat()
            save_to_json({timestamp: data})
        except json.JSONDecodeError as e:
            print(f'Error decoding JSON: {e}')
        except Exception as e:
            print(f'Error handling UDP data: {e}')


def run_http_server():
    server_address = ('', 3000)
    httpd = HTTPServer(server_address, HttpHandler)
    print('HTTP server started on port 3000')
    httpd.serve_forever()


if __name__ == '__main__':
    http_thread = threading.Thread(target=run_http_server)
    udp_thread = threading.Thread(target=udp_server)


    http_thread.start()
    udp_thread.start()


    http_thread.join()
    udp_thread.join()
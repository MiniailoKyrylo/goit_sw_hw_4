from http.server import BaseHTTPRequestHandler, HTTPServer
import mimetypes
import pathlib
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import json
import socket
import os
from threading import Thread

# Клас для обробки HTTP запитів
class RequestHandler(BaseHTTPRequestHandler):
    # Метод для обробки GET запитів
    def do_GET(self):

        # Отримуємо шлях запиту
        path = urlparse(self.path).path

        # Відправляємо відповідь залежно від шляху
        if path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('index.html', 'rb') as file:
                self.wfile.write(file.read())
        elif path == '/message':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('message.html', 'rb') as file:
                self.wfile.write(file.read())
        else:
            if pathlib.Path().joinpath(path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    # Метод для обробки POST запитів
    def do_POST(self):

        # Отримуємо шлях запиту
        path = urlparse(self.path).path

        # Обробляємо тільки POST запити на '/message'
        if path == '/message':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            # Розпаковуємо дані форми
            data = parse_qs(post_data.decode())

            # Отримуємо дані з форми
            username = data.get('username', [''])[0]
            message = data.get('message', [''])[0]
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

            # Відправляємо дані на Socket сервер
            handle_form_data({'timestamp': timestamp, 'username': username, 'message': message})

            # Перенаправляємо користувача на головну сторінку
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
        else:
            self.send_html_file('error.html', 404)
        
    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

# Функція для запуску HTTP сервера
def run_http_server():
    server_address = ('', 3000)
    httpd = HTTPServer(server_address, RequestHandler)
    httpd.serve_forever()

# Функція для обробки форми та відправки даних на Socket сервер
def handle_form_data(data):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        server_address = ('localhost', 5000)
        sock.sendto(json.dumps(data).encode(), server_address)

# Функція для обробки даних на Socket сервері та збереження їх у файлі data.json
def handle_socket_data():
    os.makedirs('storage', exist_ok=True)
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            server_address = ('localhost', 5000)
            sock.bind(server_address)

            data, _ = sock.recvfrom(4096)
            data_dict = json.loads(data.decode())

            timestamp = data_dict['timestamp']
            filename = os.path.join('storage', 'data.json')

            # Зберігаємо дані у файл data.json
            with open(filename, 'a+') as file:
                json.dump({timestamp: data_dict}, file)
                file.write('\n')
        
if __name__ == '__main__':
    # Запускаємо HTTP сервер у окремому потоці
    http_thread = Thread(target=run_http_server)
    http_thread.start()

    # Запускаємо Socket сервер у окремому потоці
    socket_thread = Thread(target=handle_socket_data)
    socket_thread.start()
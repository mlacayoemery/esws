import os
import __main__

import http.server
import socketserver

PORT = 8001
HOST = "127.0.0.1"
DIR = os.path.dirname(os.path.realpath(__main__.__file__))

os.chdir(DIR)

Handler = http.server.SimpleHTTPRequestHandler

httpd = socketserver.TCPServer((HOST, PORT), Handler)
print("serving at port", PORT)
httpd.serve_forever()

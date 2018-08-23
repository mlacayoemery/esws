import os
import SimpleHTTPServer
import SocketServer

data_path = "/home/mlacayo/workspace/cas/data"
os.chdir(data_path)

PORT = 8000

Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
httpd = SocketServer.TCPServer(("", PORT), Handler)

print "serving at port", PORT
httpd.serve_forever()

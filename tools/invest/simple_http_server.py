import os
import SimpleHTTPServer
import SocketServer

data_path = "/home/mlacayo/workspace/cas/data"
os.chdir(data_path)

PORT = 8000

Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
Handler.extensions_map.update({
    '.csv': 'text/csv',})

httpd = SocketServer.TCPServer(("localhost", PORT), Handler)

print "serving at port", PORT
httpd.serve_forever()

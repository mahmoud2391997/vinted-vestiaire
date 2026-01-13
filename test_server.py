#!/usr/bin/env python3
import sys
import os

# Change to the api directory
os.chdir('api')
sys.path.append('.')

from http.server import HTTPServer, BaseHTTPRequestHandler
from index import handler

if __name__ == "__main__":
    try:
        server = HTTPServer(('localhost', 8093), handler)
        print('Server running on http://localhost:8093')
        print('Try these URLs:')
        print('- http://localhost:8093/')
        print('- http://localhost:8093/?search=dior%20bag&pages=2')
        print('- http://localhost:8093/?search=bags&pages=2')
        server.serve_forever()
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

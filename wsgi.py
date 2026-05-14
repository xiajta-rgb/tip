# WSGI configuration for patent_crawler project
# Static file server with JSON and output directory support

import os
import sys
import mimetypes

project_home = '/home/tip/patent_crawler'

# Add project to path
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.chdir(project_home)

# Simple WSGI app for static files + JSON API
def application(environ, start_response):
    path_info = environ.get('PATH_INFO', '/')
    
    # Default to index.html
    if path_info == '/' or path_info == '':
        path_info = '/frontend/index.html'
    
    # Build full file path
    if path_info.startswith('/'):
        file_path = os.path.join(project_home, path_info[1:])
    else:
        file_path = os.path.join(project_home, path_info)
    
    # Check if file exists
    if os.path.isfile(file_path):
        # Determine content type
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            if file_path.endswith('.js'):
                content_type = 'application/javascript'
            elif file_path.endswith('.css'):
                content_type = 'text/css'
            elif file_path.endswith('.html'):
                content_type = 'text/html'
            elif file_path.endswith('.json'):
                content_type = 'application/json'
            elif file_path.endswith('.png'):
                content_type = 'image/png'
            elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                content_type = 'image/jpeg'
            elif file_path.endswith('.pdf'):
                content_type = 'application/pdf'
            else:
                content_type = 'application/octet-stream'
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            start_response('200 OK', [('Content-Type', content_type)])
            return [content]
        except Exception as e:
            start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
            return [f'Error reading file: {str(e)}'.encode()]
    else:
        # File not found
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        return [b'File not found: ' + path_info.encode()]
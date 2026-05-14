# WSGI configuration for patent_crawler static frontend
# for PythonAnywhere deployment

import sys
import os

# Project configuration
project_home = '/home/tip/tip'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.chdir(project_home)

def application(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    
    # Serve frontend/index.html for root
    if path == '/' or path == '/index.html':
        path = '/frontend/index.html'
    
    # Map URL path to file path
    file_path = os.path.join(project_home, path.lstrip('/'))
    
    # Default MIME types
    mime_types = {
        '.html': 'text/html; charset=utf-8',
        '.css': 'text/css; charset=utf-8',
        '.js': 'application/javascript; charset=utf-8',
        '.json': 'application/json; charset=utf-8',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.pdf': 'application/pdf',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',
    }
    
    # Check if file exists
    if os.path.isfile(file_path):
        ext = os.path.splitext(file_path)[1].lower()
        content_type = mime_types.get(ext, 'application/octet-stream')
        
        try:
            if ext in ['.png', '.jpg', '.jpeg', '.gif', '.pdf', '.ico']:
                with open(file_path, 'rb') as f:
                    content = f.read()
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().encode('utf-8')
            
            start_response('200 OK', [
                ('Content-Type', content_type),
                ('Content-Length', str(len(content))),
            ])
            return [content]
        except Exception as e:
            start_response('500 Internal Server Error', [
                ('Content-Type', 'text/plain; charset=utf-8'),
            ])
            return [f'Error reading file: {str(e)}'.encode('utf-8')]
    else:
        start_response('404 Not Found', [
            ('Content-Type', 'text/plain; charset=utf-8'),
        ])
        return [f'Not Found: {path}'.encode('utf-8')]

#!/usr/bin/env python3
"""
专利数据展示前端服务器

使用方法：
    python serve.py
    然后访问 http://localhost:8080
"""

import http.server
import socketserver
import os
import webbrowser
import sys

PORT = 8082
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")

def main():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"\n{'='*60}")
        print(f"🚀 专利数据展示服务器已启动")
        print(f"{'='*60}")
        print(f"\n📍 访问地址: http://localhost:{PORT}")
        print(f"📂 项目目录: {DIRECTORY}")
        print(f"\n💡 提示: 按 Ctrl+C 停止服务器\n")
        
        # 自动打开浏览器
        url = f"http://localhost:{PORT}/frontend/index.html"
        print(f"🌐 正在打开浏览器...")
        webbrowser.open(url)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n\n👋 服务器已停止")
            sys.exit(0)

if __name__ == "__main__":
    main()

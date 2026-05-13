import time
print("等待 60 秒后运行 main.py...")
time.sleep(60)

import subprocess
result = subprocess.run(['python', 'main.py', '--keyword', 'nike', '--limit', '50'], cwd='c:\\Users\\xiajt\\Desktop\\patent_crawler')
print(f"退出码: {result.returncode}")

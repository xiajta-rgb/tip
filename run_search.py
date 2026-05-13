import time
print("等待 180 秒后运行 search_design_patents.py...")
time.sleep(180)

import subprocess
result = subprocess.run(['python', 'search_design_patents.py'], cwd='c:\\Users\\xiajt\\Desktop\\patent_crawler')
print(f"退出码: {result.returncode}")

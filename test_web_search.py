import requests
from urllib.parse import quote
import re

# 尝试直接访问 Google Patents 搜索页面
url = 'https://patents.google.com/'
params = {
    'q': 'nike kind:D',
    'oq': 'nike kind:D',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

resp = requests.get(url, params=params, headers=headers, timeout=30)
print(f'Status: {resp.status_code}')
print(f'URL: {resp.url}')

# 查找专利号
patents = re.findall(r'href="/patent/([^/"]+)', resp.text)
print(f'Found {len(patents)} patents')
for p in patents[:20]:
    print(f'  {p}')

import requests
from urllib.parse import quote
import re
from bs4 import BeautifulSoup

# 尝试直接访问 Google Patents 搜索页面
url = 'https://patents.google.com/'
params = {
    'q': 'nike kind:D',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

resp = requests.get(url, params=params, headers=headers, timeout=30)
print(f'Status: {resp.status_code}')
print(f'URL: {resp.url}')
print(f'Content length: {len(resp.text)}')

# 查找专利号
soup = BeautifulSoup(resp.text, 'html.parser')
patents = soup.find_all('a', href=True)
design_patents = []
for a in patents:
    href = a['href']
    if '/patent/' in href:
        patent_id = href.split('/patent/')[1].split('/')[0]
        if 'D' in patent_id:
            design_patents.append(patent_id)

print(f'Found {len(design_patents)} design patents')
for p in design_patents[:10]:
    print(f'  {p}')

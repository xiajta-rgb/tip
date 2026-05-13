import time
import requests
from urllib.parse import quote

print("等待 30 秒后重试...")
time.sleep(30)

url = 'https://patents.google.com/xhr/query'
query = 'nike garment'
params = {
    'url': f'q={quote(query)}&num=50',
    'exp': '',
    'content': '1'
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

try:
    resp = requests.get(url, params=params, headers=headers, timeout=30)
    print(f'Status: {resp.status_code}')
    
    if resp.status_code == 200:
        data = resp.json()
        clusters = data.get('results', {}).get('cluster', [])
        count = 0
        design_count = 0
        for cluster in clusters:
            for result in cluster.get('result', []):
                patent = result.get('patent', {})
                pub_num = patent.get('publication_number', '')
                title = patent.get('title', '')[:60]
                kind = patent.get('kind', '')
                is_design = 'D' in pub_num or kind == 'D'
                if is_design:
                    design_count += 1
                print(f'{pub_num} (kind={kind}): {title} [design={is_design}]')
                count += 1
        print(f'Total: {count}, Design: {design_count}')
    else:
        print(f'Error: {resp.text[:200]}')
except Exception as e:
    print(f'Error: {e}')

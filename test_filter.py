import requests
from urllib.parse import quote

# 尝试使用 Google Patents 的 advanced search 参数
url = 'https://patents.google.com/xhr/query'

# 使用 kind:D 作为 filter
params = {
    'url': f'q=nike&f=kind:D&num=20',
    'exp': '',
    'content': '1'
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

resp = requests.get(url, params=params, headers=headers, timeout=30)
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

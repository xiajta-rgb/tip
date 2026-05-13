import requests

# 尝试 USPTO Open Data Portal API (不需要 API Key)
url = 'https://api.uspto.gov/api/v1/patent/applications/search'

# 外观专利的专利号格式: USD*
query = 'nike AND publication_number:USD*'

params = {
    'q': query,
    'rows': 20,
    'start': 0,
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
}

resp = requests.get(url, params=params, headers=headers, timeout=30)
print(f'Status: {resp.status_code}')
print(f'URL: {resp.url}')

if resp.status_code == 200:
    data = resp.json()
    docs = data.get('response', {}).get('docs', [])
    print(f'Found {len(docs)} patents')
    for doc in docs[:10]:
        pub_num = doc.get('publicationNumber', '')
        title = doc.get('inventionTitle', '')[:60]
        print(f'  {pub_num}: {title}')
else:
    print(f'Error: {resp.text[:200]}')

#!/usr/bin/env python3
import requests
from urllib.parse import quote
import json

print("Testing Google Patents API...")

url = 'https://patents.google.com/xhr/query'
params = {
    'url': f'q={quote("Patagonia")}&num=5',
    'exp': '',
    'content': '1'
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
}

try:
    print("Making request...")
    response = requests.get(url, params=params, headers=headers, timeout=15)
    print(f"Status: {response.status_code}")
    print(f"Response length: {len(response.text)}")

    if response.status_code == 200:
        data = response.json()
        print(f"Keys: {list(data.keys())}")
        clusters = data.get('results', {}).get('cluster', [])
        print(f"Clusters: {len(clusters)}")
        for i, cluster in enumerate(clusters[:2]):
            results = cluster.get('result', [])
            print(f"Cluster {i}: {len(results)} results")
    else:
        print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
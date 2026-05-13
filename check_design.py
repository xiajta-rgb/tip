import json

with open('output/patent_report_latest.json', encoding='utf-8') as f:
    data = json.load(f)
patents = data.get('patents', [])
design = [p for p in patents if 'D' in p.get('patent_number', '')]
print(f'Total: {len(patents)}, Design: {len(design)}')
for p in design[:10]:
    print(f"  {p['patent_number']}: {p['title'][:60]}")

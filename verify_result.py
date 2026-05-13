import json

with open('output/patent_report_latest.json', encoding='utf-8') as f:
    data = json.load(f)

patents = data.get('patents', [])
print(f'总专利数: {len(patents)}')
print(f'全部是外观专利: {all("D" in p.get("patent_number", "") for p in patents)}')

if patents:
    print(f'第一条: {patents[0]["patent_number"]} - {patents[0]["title"]}')
    print(f'最后一条: {patents[-1]["patent_number"]} - {patents[-1]["title"]}')

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.uspto_search import USPTOSearcher

searcher = USPTOSearcher()
patents = searcher._search_via_google_patents("nike garment", 50)
print(f"\n找到 {len(patents)} 条外观专利")
for p in patents[:5]:
    print(f"  {p['patent_number']}: {p['title'][:60]}")

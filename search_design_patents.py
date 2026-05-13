#!/usr/bin/env python3
"""
直接检索外观专利并保存结果
"""
import sys
import os
import json
import time
sys.path.insert(0, os.path.dirname(__file__))

from src.uspto_search import USPTOSearcher
from src.report_generator import ReportGenerator
from config import GARMENT_KEYWORDS

def main():
    keyword = "nike garment"
    limit = 50
    
    print(f"检索关键词: {keyword}")
    print(f"限制: {limit} 条")
    
    # 创建检索器
    searcher = USPTOSearcher()
    
    # 直接调用 _search_via_google_patents 获取外观专利
    print("\n开始检索外观专利...")
    patents = searcher._search_via_google_patents(keyword, limit)
    
    if not patents:
        print("未找到外观专利")
        return 1
    
    print(f"\n找到 {len(patents)} 条外观专利")
    
    # 服装行业筛选
    print("\n服装行业筛选...")
    garment_patents = []
    for p in patents:
        text = ' '.join([
            p.get('title', ''),
            p.get('abstract', ''),
            p.get('ipc_classification', ''),
            p.get('cpc_classification', ''),
            p.get('assignee', ''),
        ]).lower()
        
        if any(kw in text for kw in GARMENT_KEYWORDS):
            garment_patents.append(p)
    
    print(f"服装相关外观专利: {len(garment_patents)} 条")
    
    if not garment_patents:
        print("无服装相关外观专利")
        return 1
    
    # 保存结果
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(output_dir, f"patent_report_{timestamp}.json")
    
    report = {
        "metadata": {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "crawl_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_patents": len(garment_patents),
            "source": "Google Patents API (Design Patents Only)"
        },
        "patents": garment_patents
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到: {json_path}")
    
    # 创建 latest 链接
    latest_path = os.path.join(output_dir, "patent_report_latest.json")
    with open(latest_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"最新结果已保存到: {latest_path}")
    
    # 显示前 5 条专利
    print("\n前 5 条外观专利:")
    for i, p in enumerate(garment_patents[:5], 1):
        print(f"  {i}. {p['patent_number']} - {p['title'][:60]}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

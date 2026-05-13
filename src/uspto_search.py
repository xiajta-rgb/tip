#!/usr/bin/env python3
"""
USPTO 专利检索模块
支持通过 USPTO Patent Public Search Basic 检索专利
"""

import json
import time
import re
from typing import List, Dict, Optional
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import (
    USPTO_SEARCH_URL,
    RESULTS_PER_PAGE,
    REQUEST_TIMEOUT,
    USE_PROXY,
    PROXY_URL,
    MAX_RETRIES,
)


class USPTOSearcher:
    """USPTO 专利检索器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
        # 配置重试策略
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 代理设置
        if USE_PROXY:
            self.session.proxies = {
                'http': PROXY_URL,
                'https': PROXY_URL,
            }
    
    def search_by_keyword(self, keyword: str, limit: int = 50) -> List[Dict]:
        """
        通过关键词检索专利
        
        Args:
            keyword: 检索关键词
            limit: 最大结果数量
            
        Returns:
            专利列表，每项包含 patent_number, title, inventor, publication_date, link
        """
        print(f"🔍 正在检索关键词: '{keyword}'...")
        
        # 使用 Google Patents API 作为数据源（更稳定）
        patents = self._search_via_google_patents(keyword, limit)
        
        if not patents:
            print(f"⚠️ 未找到与 '{keyword}' 相关的专利")
        else:
            print(f"✅ 找到 {len(patents)} 条相关专利")
            
        return patents
    
    def _search_via_google_patents(self, query: str, num_results: int = 50) -> List[Dict]:
        """通过 Google Patents API 检索"""
        url = "https://patents.google.com/xhr/query"
        params = {
            'url': f'q={quote(query)}&num={min(num_results, 100)}',
            'exp': '',
            'content': '1'
        }
        
        try:
            response = self.session.get(
                url, 
                params=params, 
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            patents = []
            
            for cluster in data.get('results', {}).get('cluster', []):
                for result in cluster.get('result', []):
                    patent = result.get('patent', {})
                    if not patent:
                        continue
                        
                    pub_num = patent.get('publication_number', '')
                    if not pub_num:
                        continue
                    
                    # 解析专利类型
                    pub_type = self._determine_patent_type(pub_num)
                    
                    # 构建链接
                    uspto_link = f"https://ppubs.uspto.gov/pubwebapp/?patentNumber={pub_num}"
                    
                    patents.append({
                        'patent_number': pub_num,
                        'title': self._clean_html(patent.get('title', '')),
                        'inventor': patent.get('inventor', 'Not listed'),
                        'assignee': patent.get('assignee', 'Not listed'),
                        'publication_date': patent.get('publication_date', ''),
                        'filing_date': patent.get('filing_date', ''),
                        'type': pub_type,
                        'link': uspto_link,
                        'snippet': self._clean_html(patent.get('snippet', '')),
                    })
                    
                    if len(patents) >= num_results:
                        break
                if len(patents) >= num_results:
                    break
                    
            return patents
            
        except Exception as e:
            print(f"❌ Google Patents 检索失败: {e}")
            return []
    
    def _determine_patent_type(self, patent_number: str) -> str:
        """根据专利号判断类型"""
        if 'D' in patent_number:
            return "外观设计专利"
        elif patent_number.endswith('B1'):
            return "实用专利(B1)"
        elif patent_number.endswith('B2'):
            return "实用专利(B2)"
        elif patent_number.endswith('A1'):
            return "申请公开(A1)"
        elif patent_number.endswith('A2'):
            return "申请公开(A2)"
        elif 'S' in patent_number:
            return "外观设计专利"
        else:
            return "未知类型"
    
    def _clean_html(self, text: str) -> str:
        """清理 HTML 标签"""
        if not text:
            return ""
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)
        # 解码 HTML 实体
        text = text.replace('&quot;', '"').replace('&amp;', '&')
        text = text.replace('&lt;', '<').replace('&gt;', '>')
        return text.strip()
    
    def search_multiple_keywords(self, keywords: List[str], limit_per_keyword: int = 20) -> List[Dict]:
        """
        批量检索多个关键词
        
        Args:
            keywords: 关键词列表
            limit_per_keyword: 每个关键词的最大结果数
            
        Returns:
            合并后的专利列表（去重）
        """
        all_patents = []
        seen_numbers = set()
        
        for keyword in keywords:
            patents = self.search_by_keyword(keyword, limit_per_keyword)
            
            for p in patents:
                if p['patent_number'] not in seen_numbers:
                    seen_numbers.add(p['patent_number'])
                    all_patents.append(p)
            
            time.sleep(1)  # 避免请求过快
        
        # 按日期排序
        all_patents.sort(
            key=lambda x: x.get('publication_date', '0000-00-00'), 
            reverse=True
        )
        
        return all_patents


def main():
    """测试检索功能"""
    searcher = USPTOSearcher()
    
    # 测试单个关键词
    results = searcher.search_by_keyword("garment", limit=10)
    
    print("\n" + "="*60)
    print("检索结果预览:")
    print("="*60)
    
    for i, p in enumerate(results[:5], 1):
        print(f"\n[{i}] {p['patent_number']}")
        print(f"    标题: {p['title'][:60]}...")
        print(f"    发明人: {p['inventor']}")
        print(f"    日期: {p['publication_date']}")
        print(f"    类型: {p['type']}")


if __name__ == "__main__":
    main()

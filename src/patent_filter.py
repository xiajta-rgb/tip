#!/usr/bin/env python3
"""
专利分类筛选模块

功能：
1. 从 CSV 或列表获取专利 ID
2. 用 Google Patents API 获取详细信息（标题、摘要等）
3. 用配置好的分类关键词筛选专利标题
"""

import time
import re
from typing import List, Dict, Optional, Set
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    CATEGORY_KEYWORDS,
    CATEGORY_ALIASES,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
)


class PatentFilter:
    """专利分类筛选器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _build_keyword_set(self) -> Set[str]:
        """构建所有关键词集合（包含别名）"""
        keywords = set()
        
        # 添加原始关键词
        for kw in CATEGORY_KEYWORDS:
            keywords.add(kw.lower())
        
        # 添加别名
        for canonical, aliases in CATEGORY_ALIASES.items():
            keywords.add(canonical.lower())
            for alias in aliases:
                keywords.add(alias.lower())
        
        return keywords
    
    def _match_keywords(self, text: str) -> List[str]:
        """
        在文本中匹配分类关键词
        
        Args:
            text: 要搜索的文本（标题等）
            
        Returns:
            匹配的关键词列表
        """
        text_lower = text.lower()
        matched = []
        keyword_set = self._build_keyword_set()
        
        for keyword in keyword_set:
            if keyword in text_lower:
                matched.append(keyword)
        
        return matched
    
    def _fetch_patent_details(self, patent_number: str) -> Optional[Dict]:
        """
        获取专利详细信息
        
        Args:
            patent_number: 专利号
            
        Returns:
            详细信息字典
        """
        try:
            # 直接访问 HTML 页面
            url = f"https://patents.google.com/patent/{patent_number}/en"
            
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            title_el = soup.find(attrs={"itemprop": "title"})
            title = title_el.get_text(strip=True) if title_el else ''
            
            # 提取摘要
            abstract_el = soup.find(attrs={"itemprop": "abstract"})
            abstract = abstract_el.get_text(strip=True) if abstract_el else ''
            if abstract.startswith('Abstract'):
                abstract = abstract[8:].strip()
            
            # 提取法律状态
            legal_status = ''
            events = soup.find_all(attrs={"itemprop": "legalEvents"})
            for event in reversed(events):
                title_el = event.find(attrs={"itemprop": "title"})
                if title_el:
                    t = title_el.get_text(strip=True).lower()
                    if 'expired' in t or 'lapse' in t:
                        legal_status = 'Expired'
                        break
                    elif 'grant' in t or 'patent' in t:
                        legal_status = 'Active'
            
            if not legal_status:
                status_el = soup.find(attrs={"itemprop": "status"})
                if status_el:
                    legal_status = status_el.get_text(strip=True)
            
            return {
                'title': title,
                'abstract': abstract,
                'legal_status': legal_status,
            }
            
        except Exception as e:
            print(f"  ⚠️ 获取 {patent_number} 详情失败: {str(e)[:50]}")
            return None
    
    def enrich_and_filter(self, patents: List[Dict], 
                         include_expired: bool = False,
                         required_keywords: List[str] = None,
                         limit: int = 50) -> List[Dict]:
        """
        获取专利详细信息并按关键词筛选
        
        Args:
            patents: 专利列表（包含 patent_number）
            include_expired: 是否包含过期专利
            required_keywords: 必须包含的关键词列表（可选）
            limit: 最大处理数量
            
        Returns:
            筛选后的专利列表
        """
        print(f"\n{'='*60}")
        print(f"🔍 开始获取专利详情并筛选...")
        print(f"{'='*60}")
        
        # 构建必须匹配的关键词集合
        required_set = set()
        if required_keywords:
            for kw in required_keywords:
                required_set.add(kw.lower())
            print(f"📋 必须匹配关键词: {', '.join(required_keywords)}")
        
        results = []
        total = min(len(patents), limit)
        
        for i, patent in enumerate(patents[:limit], 1):
            pub_num = patent.get('patent_number', '')
            if not pub_num:
                continue
            
            print(f"  [{i}/{total}] 处理 {pub_num}...")
            
            # 获取详细信息
            details = self._fetch_patent_details(pub_num)
            
            if details:
                patent.update(details)
                
                # 合并标题和摘要进行匹配
                text_to_search = f"{details.get('title', '')} {details.get('abstract', '')}"
                use_original_title = False
                
                # 检查是否包含必需关键词
                if required_set:
                    matched = self._match_keywords(text_to_search)
                    if not any(kw.lower() in required_set for kw in matched):
                        print(f"    ⏭️ 跳过: 未包含必需关键词")
                        continue
                
                # 检查是否匹配分类关键词
                matched_keywords = self._match_keywords(text_to_search)
                if matched_keywords:
                    patent['matched_keywords'] = matched_keywords
                    print(f"    ✅ 匹配: {', '.join(matched_keywords[:5])}")
                else:
                    print(f"    ⏭️ 跳过: 未匹配分类关键词")
                    continue
                
                # 检查法律状态
                if not include_expired and details.get('legal_status') == 'Expired':
                    print(f"    ⏭️ 跳过: 专利已过期")
                    continue
                
                results.append(patent)
            else:
                # 如果 API 失败，使用 CSV 中的标题
                if patent.get('title'):
                    text_to_search = patent['title']
                    use_original_title = True
                    matched_keywords = self._match_keywords(text_to_search)
                    if matched_keywords:
                        patent['matched_keywords'] = matched_keywords
                        results.append(patent)
            
            time.sleep(0.3)
        
        print(f"\n✅ 筛选完成: {len(results)}/{total} 条专利符合条件")
        return results


def main():
    """测试筛选功能"""
    from src.brand_search import BrandPatentSearcher
    
    print("="*60)
    print("🧪 测试 Patagonia 品牌专利筛选")
    print("="*60)
    
    # 1. 获取品牌专利
    searcher = BrandPatentSearcher(headless=False)
    patents = searcher.search_brand_patents("Patagonia", limit=50)
    print(f"\n📋 从 USPTO 获取到 {len(patents)} 条专利")
    
    if not patents:
        print("❌ 未获取到专利")
        return
    
    # 2. 筛选
    filter = PatentFilter()
    filtered = filter.enrich_and_filter(
        patents,
        include_expired=False,
        limit=50
    )
    
    # 3. 显示结果
    print(f"\n{'='*60}")
    print(f"📊 筛选结果: {len(filtered)} 条")
    print(f"{'='*60}")
    
    for i, p in enumerate(filtered, 1):
        print(f"\n{i}. {p.get('patent_number', 'N/A')}")
        print(f"   标题: {p.get('title', p.get('title', 'N/A'))[:80]}...")
        if p.get('matched_keywords'):
            print(f"   匹配: {', '.join(p.get('matched_keywords', []))}")
    
    print(f"\n✅ 完成")


if __name__ == "__main__":
    main()
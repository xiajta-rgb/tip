#!/usr/bin/env python3
"""
专利详情获取模块 - 使用 Playwright

功能：
1. 从 CSV 或列表获取专利 ID
2. 用 Playwright 访问专利页面获取详细信息
3. 用配置好的分类关键词筛选专利标题
"""

import asyncio
import csv
import os
import time
from typing import List, Dict, Optional, Set
from playwright.async_api import async_playwright

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    CATEGORY_KEYWORDS,
    CATEGORY_ALIASES,
)


class PatentDetailFetcher:
    """使用 Playwright 获取专利详情"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
    
    async def init(self):
        """初始化浏览器"""
        p = await async_playwright().start()
        self.browser = await p.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
    
    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
    
    async def fetch_detail(self, patent_number: str) -> Optional[Dict]:
        """
        获取单个专利详情
        
        Args:
            patent_number: 专利号
            
        Returns:
            详细信息字典
        """
        try:
            url = f"https://patents.google.com/patent/{patent_number}/en"
            await self.page.goto(url, timeout=30000)
            await self.page.wait_for_load_state("domcontentloaded", timeout=30000)
            
            # 等待页面加载
            await asyncio.sleep(2)
            
            # 提取标题
            title = ""
            title_el = await self.page.query_selector("[itemprop='title']")
            if title_el:
                title = await title_el.inner_text()
            
            # 提取摘要
            abstract = ""
            abstract_el = await self.page.query_selector("[itemprop='abstract']")
            if abstract_el:
                abstract = await abstract_el.inner_text()
                if abstract.startswith("Abstract"):
                    abstract = abstract[8:].strip()
            
            # 提取申请人/受让人
            assignee = ""
            assignee_el = await self.page.query_selector("[itemprop='assigneeName']")
            if not assignee_el:
                assignee_el = await self.page.query_selector("assignee-name")
            if assignee_el:
                assignee = await assignee_el.inner_text()
            
            # 提取发明人
            inventor = ""
            inventor_els = await self.page.query_selector_all("[itemprop='inventor']")
            if inventor_els:
                inventors = []
                for el in inventor_els:
                    text = await el.inner_text()
                    if text:
                        inventors.append(text)
                inventor = ", ".join(inventors)
            
            return {
                'title': title.strip() if title else '',
                'abstract': abstract.strip() if abstract else '',
                'assignee': assignee.strip() if assignee else '',
                'inventor': inventor.strip() if inventor else '',
            }
            
        except Exception as e:
            return None
    
    async def enrich_and_filter(self, patents: List[Dict],
                               include_expired: bool = False,
                               limit: int = 50) -> List[Dict]:
        """
        获取专利详情并按关键词筛选
        
        Args:
            patents: 专利列表（包含 patent_number）
            include_expired: 是否包含过期专利
            limit: 最大处理数量
            
        Returns:
            筛选后的专利列表
        """
        print(f"\n{'='*60}")
        print(f"🔍 使用 Playwright 获取专利详情并筛选...")
        print(f"{'='*60}")
        
        results = []
        total = min(len(patents), limit)
        
        for i, patent in enumerate(patents[:limit], 1):
            pub_num = patent.get('patent_number', '')
            if not pub_num:
                continue
            
            print(f"  [{i}/{total}] 获取 {pub_num} 详情...")
            
            details = await self.fetch_detail(pub_num)
            
            if details:
                patent.update(details)
                title = details.get('title', '')
                abstract = details.get('abstract', '')
                text_to_search = f"{title} {abstract}"
            else:
                # 使用 CSV 中的标题
                title = patent.get('title', '')
                text_to_search = title
            
            # 匹配关键词
            matched_keywords = self._match_keywords(text_to_search)
            
            if matched_keywords:
                patent['matched_keywords'] = matched_keywords
                print(f"    ✅ 匹配: {', '.join(matched_keywords[:5])}")
                results.append(patent)
            else:
                print(f"    ⏭️ 未匹配分类关键词")
            
            await asyncio.sleep(1)  # 避免请求过快
        
        print(f"\n✅ 筛选完成: {len(results)}/{total} 条专利符合条件")
        return results
    
    def _build_keyword_set(self) -> Set[str]:
        """构建所有关键词集合（包含别名）"""
        keywords = set()
        for kw in CATEGORY_KEYWORDS:
            keywords.add(kw.lower())
        for canonical, aliases in CATEGORY_ALIASES.items():
            keywords.add(canonical.lower())
            for alias in aliases:
                keywords.add(alias.lower())
        return keywords
    
    def _match_keywords(self, text: str) -> List[str]:
        """在文本中匹配分类关键词"""
        text_lower = text.lower()
        matched = []
        for keyword in self._build_keyword_set():
            if keyword in text_lower:
                matched.append(keyword)
        return matched


async def main():
    """测试"""
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from src.brand_search_async import BrandPatentSearcher
    
    print("="*60)
    print("测试 Playwright 获取专利详情")
    print("="*60)
    
    # 1. 获取品牌专利
    searcher = BrandPatentSearcher(headless=False)
    patents = await searcher.search_and_export("Patagonia", limit=20)
    print(f"\n从 USPTO 获取到 {len(patents)} 条专利")
    
    if patents:
        # 2. 获取详情并筛选
        fetcher = PatentDetailFetcher(headless=False)
        await fetcher.init()
        try:
            filtered = await fetcher.enrich_and_filter(patents, limit=20)
            
            print(f"\n{'='*60}")
            print(f"📊 筛选结果: {len(filtered)} 条")
            print(f"{'='*60}")
            
            for i, p in enumerate(filtered[:10], 1):
                title = p.get('title', 'N/A')
                if len(title) > 60:
                    title = title[:60] + "..."
                print(f"\n{i}. {p.get('patent_number')}")
                print(f"   标题: {title}")
                print(f"   匹配: {p.get('matched_keywords', [])}")
        finally:
            await fetcher.close()
    
    print("\n✅ 完成")


if __name__ == "__main__":
    asyncio.run(main())
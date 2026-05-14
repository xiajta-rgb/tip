#!/usr/bin/env python3
"""
完整品牌专利搜索流程

流程：
1. 在 https://ppubs.uspto.gov/basic/# 搜索品牌词获取专利 ID
2. 用 Playwright 获取每个专利的详细信息
3. 用配置好的分类关键词筛选 title 字段
"""

import asyncio
import csv
import os
from typing import List, Dict, Set
from playwright.async_api import async_playwright

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CATEGORY_KEYWORDS, CATEGORY_ALIASES, HEADLESS


class BrandPatentSearcher:
    """品牌专利搜索器 - 完整流程"""
    
    def __init__(self, headless: bool = HEADLESS, download_dir: str = None):
        self.headless = headless
        self.download_dir = download_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "downloads")
        os.makedirs(self.download_dir, exist_ok=True)
    
    def _build_all_keywords(self) -> Set[str]:
        """构建所有关键词集合（包含别名）"""
        keywords = set()
        for kw in CATEGORY_KEYWORDS:
            keywords.add(kw.lower())
        for canonical, aliases in CATEGORY_ALIASES.items():
            keywords.add(canonical.lower())
            for alias in aliases:
                keywords.add(alias.lower())
        return keywords
    
    async def search_and_export(self, brand: str, limit: int = 50) -> List[Dict]:
        """在 basic 页面搜索品牌词并导出 CSV"""
        print(f"\n{'='*60}")
        print(f"🔍 在 basic 页面搜索品牌 '{brand}' 并导出 CSV...")
        print(f"{'='*60}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()
            
            try:
                # 访问 basic 页面
                await page.goto("https://ppubs.uspto.gov/basic/#")
                await asyncio.sleep(3)
                
                # 查找 ID 输入框并输入品牌名
                print("📍 等待 ID 输入框...")
                
                # 方法1: 尝试多种选择器
                id_input = None
                selectors = [
                    "input[placeholder*='ID']",
                    "input[id*='idInput']",
                    "input[id*='patentId']",
                    "textarea[id*='id']",
                    "#patentIds",
                    "input[type='text']",
                ]
                for sel in selectors:
                    el = await page.query_selector(sel)
                    if el:
                        id_input = el
                        print(f"✅ 找到输入框: {sel}")
                        break
                
                if not id_input:
                    print("❌ 未找到 ID 输入框，保存截图...")
                    await page.screenshot(path=os.path.join(self.download_dir, "debug_basic.png"))
                    return []
                
                # 输入品牌词
                await id_input.fill(brand)
                print(f"📝 已输入: {brand}")
                
                await asyncio.sleep(1)
                
                # 点击搜索按钮
                search_btn = None
                btn_selectors = [
                    "button[type='submit']",
                    "button:has-text('Search')",
                    "button:has-text('search')",
                    "#searchBtn",
                ]
                for sel in btn_selectors:
                    el = await page.query_selector(sel)
                    if el:
                        search_btn = el
                        break
                
                if search_btn:
                    await search_btn.click()
                    print("✅ 点击搜索按钮")
                else:
                    await id_input.press("Enter")
                    print("✅ 按下回车")
                
                # 等待结果
                await asyncio.sleep(5)
                
                # 点击导出按钮
                async with page.expect_download(timeout=60000) as download_info:
                    # basic 页面可能有不同的导出按钮选择器
                    export_selectors = [
                        "button.export-csv",
                        "button:has-text('Export')",
                        "button[title*='Export']",
                        "a:has-text('Export')",
                        ".export-btn",
                        "button.export",
                    ]
                    export_btn = None
                    for sel in export_selectors:
                        btn = await page.query_selector(sel)
                        if btn and await btn.is_visible():
                            export_btn = btn
                            print(f"✅ 找到导出按钮: {sel}")
                            break
                    
                    if not export_btn:
                        print("⚠️ 未找到导出按钮，保存截图...")
                        await page.screenshot(path=os.path.join(self.download_dir, "debug_export.png"))
                        # 列出所有按钮
                        buttons = await page.query_selector_all("button")
                        print(f"页面按钮: {[await b.inner_text() for b in buttons[:10]]}")
                        return []
                    
                    await export_btn.click()
                    print("📥 正在导出...")
                    download = await download_info.value
                    csv_path = os.path.join(self.download_dir, download.suggested_filename)
                    await download.save_as(csv_path)
                
                print(f"✅ CSV 已保存: {csv_path}")
                
                # 解析 CSV
                return self._parse_csv(csv_path, limit)
                
            finally:
                await browser.close()
    
    def _parse_csv(self, csv_file: str, limit: int) -> List[Dict]:
        patents = []
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                for i, row in enumerate(csv.DictReader(f)):
                    if i >= limit:
                        break
                    patents.append({
                        'patent_number': row.get('Document ID', ''),
                        'title': row.get('Title', ''),
                        'assignee': row.get('Assignee', ''),
                        'inventor': row.get('Inventor', ''),
                        'date_published': row.get('Date Published', ''),
                    })
        except Exception as e:
            print(f"⚠️ 解析 CSV 失败: {e}")
        return patents


class PatentDetailFetcher:
    """获取专利详情"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
    
    async def fetch_detail(self, patent_number: str, page) -> Optional[Dict]:
        """获取单个专利详情"""
        try:
            url = f"https://patents.google.com/patent/{patent_number}/en"
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            
            title = ""
            title_el = await page.query_selector("[itemprop='title']")
            if title_el:
                title = await title_el.inner_text()
            
            abstract = ""
            abstract_el = await page.query_selector("[itemprop='abstract']")
            if abstract_el:
                abstract = await abstract_el.inner_text()
                if abstract.startswith("Abstract"):
                    abstract = abstract[8:].strip()
            
            return {
                'title': title.strip() if title else '',
                'abstract': abstract.strip() if abstract else '',
            }
        except:
            return None
    
    async def enrich_patents(self, patents: List[Dict], limit: int = 50) -> List[Dict]:
        """获取专利详情"""
        print(f"\n{'='*60}")
        print(f"🔍 获取专利详情...")
        print(f"{'='*60}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            
            results = []
            total = min(len(patents), limit)
            
            for i, patent in enumerate(patents[:limit], 1):
                pub_num = patent.get('patent_number', '')
                if not pub_num:
                    continue
                
                print(f"  [{i}/{total}] 获取 {pub_num} 详情...")
                details = await self.fetch_detail(pub_num, page)
                
                if details:
                    patent.update(details)
                results.append(patent)
                
                await asyncio.sleep(1)
            
            await browser.close()
            return results


class PatentFilter:
    """专利筛选器 - 只匹配 title"""
    
    def __init__(self):
        self.keywords = self._build_keywords()
        print(f"📋 分类关键词数量: {len(self.keywords)}")
    
    def _build_keywords(self) -> Set[str]:
        keywords = set()
        for kw in CATEGORY_KEYWORDS:
            keywords.add(kw.lower())
        for canonical, aliases in CATEGORY_ALIASES.items():
            keywords.add(canonical.lower())
            for alias in aliases:
                keywords.add(alias.lower())
        return keywords
    
    def filter_by_title(self, patents: List[Dict]) -> List[Dict]:
        """只根据 title 字段筛选"""
        print(f"\n{'='*60}")
        print(f"🔍 筛选专利 (只匹配 title)...")
        print(f"{'='*60}")
        
        results = []
        for patent in patents:
            title = patent.get('title', '').lower()
            if not title:
                title = patent.get('title', '').lower()  # 使用 CSV 中的 title
            
            matched = []
            for keyword in self.keywords:
                if keyword in title:
                    matched.append(keyword)
            
            if matched:
                patent['matched_keywords'] = matched
                results.append(patent)
                print(f"  ✅ {patent.get('patent_number')}: 匹配 {matched}")
            else:
                print(f"  ⏭️ {patent.get('patent_number')}: 未匹配")
        
        print(f"\n✅ 筛选完成: {len(results)}/{len(patents)} 条符合条件")
        return results


async def main():
    """测试完整流程"""
    brand = "Patagonia"
    limit = 50
    
    print("="*60)
    print(f"品牌专利搜索测试: {brand}")
    print("="*60)
    
    # 1. 搜索并导出
    searcher = BrandPatentSearcher(headless=False)
    patents = await searcher.search_and_export(brand, limit=limit)
    print(f"\n📋 从 USPTO 获取到 {len(patents)} 条专利")
    
    if not patents:
        print("❌ 未获取到专利")
        return
    
    # 2. 获取详情
    fetcher = PatentDetailFetcher(headless=False)
    patents = await fetcher.enrich_patents(patents, limit=limit)
    
    # 3. 筛选
    filter = PatentFilter()
    filtered = filter.filter_by_title(patents)
    
    # 4. 输出结果
    print(f"\n{'='*60}")
    print(f"📊 最终结果: {len(filtered)} 条")
    print(f"{'='*60}")
    
    for i, p in enumerate(filtered, 1):
        print(f"\n{i}. {p.get('patent_number')}")
        print(f"   标题: {p.get('title', 'N/A')[:80]}...")
        print(f"   匹配: {p.get('matched_keywords', [])}")
    
    print("\n✅ 完成")


if __name__ == "__main__":
    asyncio.run(main())
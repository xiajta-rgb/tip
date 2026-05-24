#!/usr/bin/env python3
"""
品牌专利搜索模块

使用 Playwright 浏览器自动化 + USPTO pubwebapp CSV 导出

流程：
1. 使用 Playwright 在 pubwebapp 搜索品牌词
2. 导出搜索结果到 CSV 文件
3. 解析 CSV 文件获取专利 ID
4. 将专利 ID 用于后续 Google Patents API 搜索
"""

import asyncio
import csv
import os
from typing import List, Dict, Optional
from playwright.async_api import async_playwright

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import HEADLESS


class BrandPatentSearcher:
    """品牌专利搜索器 - 使用 Playwright"""
    
    def __init__(self, headless: bool = HEADLESS, download_dir: str = None):
        self.headless = headless
        self.download_dir = download_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")
        os.makedirs(self.download_dir, exist_ok=True)
    
    async def search_and_export(self, brand: str, limit: int = 50) -> List[Dict]:
        """
        搜索品牌词并导出 CSV 文件
        
        流程：
        1. 检查本地是否已有 {brand}.csv 缓存
        2. 如果有缓存，直接使用
        3. 如果没有，使用 Playwright 搜索并导出
        
        Args:
            brand: 品牌名称（如 Nike）
            limit: 最大结果数量
            
        Returns:
            专利列表，包含 patent_number, title, assignee 等信息
        """
        csv_filename = f"{brand}.csv"
        csv_path = os.path.join(self.download_dir, csv_filename)
        
        if os.path.exists(csv_path):
            print(f"\n{'='*60}")
            print(f"♻️  CSV 文件已存在，直接使用: {csv_path}")
            print(f"{'='*60}")
            patents = self._parse_csv(csv_path, limit)
            print(f"✅ 解析到 {len(patents)} 个专利")
            return patents
        
        print(f"\n{'='*60}")
        print(f"🔍 Playwright 搜索品牌 '{brand}' 并导出 CSV...")
        print(f"{'='*60}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(channel='msedge', headless=self.headless)
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()
            
            try:
                await page.goto("https://ppubs.uspto.gov/pubwebapp/")
                print(f"✅ 已访问: https://ppubs.uspto.gov/pubwebapp/")
                
                await page.wait_for_selector("trix-editor.trix", timeout=30000)
                print("✅ 搜索框已加载")
                
                await asyncio.sleep(2)
                await page.click("trix-editor.trix")
                await asyncio.sleep(1)
                await page.fill("trix-editor.trix", brand)
                print(f"📝 已输入: {brand}")
                
                await asyncio.sleep(1)
                await page.press("trix-editor.trix", "Enter")
                print("🔍 执行搜索...")
                
                await asyncio.sleep(10)
                
                async with page.expect_download(timeout=60000) as download_info:
                    await page.click("button.export-csv")
                    print("📥 正在导出...")
                    download = await download_info.value
                    await download.save_as(csv_path)
                
                print(f"✅ CSV 已保存: {csv_path}")
                
                patents = self._parse_csv(csv_path, limit)
                print(f"✅ 解析到 {len(patents)} 个专利")
                
                return patents
                
            finally:
                await browser.close()
    
    def _parse_csv(self, csv_file: str, limit: int) -> List[Dict]:
        patents = []
        encodings = ['utf-8-sig', 'utf-8', 'utf-16', 'latin-1', 'cp1252']
        
        for enc in encodings:
            try:
                with open(csv_file, 'r', encoding=enc) as f:
                    reader = list(csv.DictReader(f))
                    for i, row in enumerate(reader):
                        if i >= limit:
                            break
                        
                        doc_id = row.get('Document ID', '')
                        title = row.get('Title', '')
                        assignee = row.get('Assignee', '')
                        date = row.get('Date Published', '')
                        inventor = row.get('Inventor', '')
                        
                        patents.append({
                            'patent_number': doc_id,
                            'title': title,
                            'assignee': assignee,
                            'inventor': inventor,
                            'date_published': date,
                        })
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                print(f"⚠️ 解析 CSV 失败 (编码 {enc}): {str(e)}")
                continue
        
        if not patents:
            print(f"⚠️ 所有编码尝试均失败: {csv_file}")
        
        return patents
    
    def search_brand_patents(self, brand: str, limit: int = 50) -> List[Dict]:
        """
        同步接口 - 搜索品牌专利
        
        Args:
            brand: 品牌名称
            limit: 最大结果数量
            
        Returns:
            专利列表
        """
        return asyncio.run(self.search_and_export(brand, limit))


def main():
    """测试品牌专利搜索"""
    searcher = BrandPatentSearcher(headless=False)
    
    try:
        patents = searcher.search_brand_patents("Patagonia", limit=100)
        
        print(f"\n{'='*60}")
        print(f"📊 Patagonia 搜索结果: {len(patents)} 条")
        print(f"{'='*60}")
        
        for i, p in enumerate(patents[:10], 1):
            print(f"{i}. {p.get('patent_number', 'N/A')}")
            if p.get('title'):
                print(f"   标题: {p['title'][:60]}...")
            if p.get('assignee'):
                print(f"   受让人: {p['assignee']}")
            print()
        
    finally:
        print("✅ 完成")


if __name__ == "__main__":
    main()
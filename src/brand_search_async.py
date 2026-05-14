#!/usr/bin/env python3
"""
品牌专利搜索模块 - 异步版本

使用 Playwright 浏览器自动化 + USPTO pubwebapp CSV 导出
"""

import asyncio
import csv
import os
from typing import List, Dict
from playwright.async_api import async_playwright

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import HEADLESS


class BrandPatentSearcher:
    """品牌专利搜索器 - 使用 Playwright"""
    
    def __init__(self, headless: bool = HEADLESS, download_dir: str = None):
        self.headless = headless
        self.download_dir = download_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "downloads")
        os.makedirs(self.download_dir, exist_ok=True)
    
    async def search_and_export(self, brand: str, limit: int = 50) -> List[Dict]:
        """搜索品牌词并导出 CSV"""
        print(f"\n{'='*60}")
        print(f"🔍 搜索品牌 '{brand}' 并导出 CSV...")
        print(f"{'='*60}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()
            
            try:
                await page.goto("https://ppubs.uspto.gov/pubwebapp/")
                await page.wait_for_selector("trix-editor.trix", timeout=30000)
                await asyncio.sleep(2)
                await page.click("trix-editor.trix")
                await asyncio.sleep(1)
                await page.fill("trix-editor.trix", brand)
                await asyncio.sleep(1)
                await page.press("trix-editor.trix", "Enter")
                await asyncio.sleep(10)
                
                async with page.expect_download(timeout=60000) as download_info:
                    await page.click("button.export-csv")
                    download = await download_info.value
                    csv_path = os.path.join(self.download_dir, download.suggested_filename)
                    await download.save_as(csv_path)
                
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
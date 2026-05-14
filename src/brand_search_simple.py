#!/usr/bin/env python3
"""
简化版品牌专利搜索流程

流程：
1. 在 https://ppubs.uspto.gov/pubwebapp/ 搜索品牌词
2. 导出 CSV
3. 用 config.py 的关键词筛选 Title 字段
"""

import asyncio
import csv
import os
from typing import List, Dict, Set
from playwright.async_api import async_playwright

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CATEGORY_KEYWORDS, CATEGORY_ALIASES, HEADLESS


def build_keywords() -> Set[str]:
    """构建所有关键词集合"""
    keywords = set()
    for kw in CATEGORY_KEYWORDS:
        keywords.add(kw.lower())
    for canonical, aliases in CATEGORY_ALIASES.items():
        keywords.add(canonical.lower())
        for alias in aliases:
            keywords.add(alias.lower())
    return keywords


async def search_brand(brand: str, limit: int = 100) -> List[Dict]:
    """搜索品牌并导出 CSV"""
    print(f"\n{'='*60}")
    print(f"🔍 搜索品牌 '{brand}'...")
    print(f"{'='*60}")
    
    download_dir = os.path.join(os.path.dirname(__file__), "..", "downloads")
    os.makedirs(download_dir, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        
        try:
            await page.goto("https://ppubs.uspto.gov/pubwebapp/")
            await page.wait_for_selector("trix-editor.trix", timeout=30000)
            print("✅ 找到搜索框")
            
            await asyncio.sleep(2)
            await page.click("trix-editor.trix")
            await asyncio.sleep(1)
            await page.fill("trix-editor.trix", brand)
            print(f"📝 已输入: {brand}")
            
            await asyncio.sleep(1)
            await page.press("trix-editor.trix", "Enter")
            print("🔍 执行搜索...")
            
            # 等待结果
            await asyncio.sleep(10)
            
            # 导出 CSV
            async with page.expect_download(timeout=60000) as download_info:
                await page.click("button.export-csv")
                print("📥 导出中...")
                download = await download_info.value
                csv_path = os.path.join(download_dir, download.suggested_filename)
                await download.save_as(csv_path)
            
            print(f"✅ CSV: {csv_path}")
            
            # 解析
            patents = []
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                for i, row in enumerate(csv.DictReader(f)):
                    if i >= limit:
                        break
                    patents.append({
                        'patent_number': row.get('Document ID', ''),
                        'title': row.get('Title', ''),
                        'assignee': row.get('Assignee', ''),
                        'date_published': row.get('Date Published', ''),
                    })
            
            return patents
        finally:
            await browser.close()


def filter_by_title(patents: List[Dict]) -> List[Dict]:
    """只用 Title 字段筛选"""
    print(f"\n{'='*60}")
    print(f"🔍 筛选专利 (Title 匹配 config.py 关键词)...")
    print(f"{'='*60}")
    
    keywords = build_keywords()
    print(f"📋 关键词数量: {len(keywords)}")
    
    filtered = []
    for patent in patents:
        title = patent.get('title', '').lower()
        
        matched = []
        for kw in keywords:
            if kw in title:
                matched.append(kw)
        
        if matched:
            patent['matched_keywords'] = matched
            filtered.append(patent)
            print(f"  ✅ {patent.get('patent_number')}: {matched[:3]}")
        else:
            print(f"  ⏭️ {patent.get('patent_number')}: 未匹配")
    
    print(f"\n✅ 筛选结果: {len(filtered)}/{len(patents)} 条")
    return filtered


async def main():
    brand = "Patagonia"
    limit = 100
    
    print("="*60)
    print(f"品牌专利搜索: {brand}")
    print("="*60)
    
    # 1. 搜索
    patents = await search_brand(brand, limit=limit)
    print(f"\n📋 获取到 {len(patents)} 条专利")
    
    if not patents:
        print("❌ 未获取到专利")
        return
    
    # 2. 筛选
    filtered = filter_by_title(patents)
    
    # 3. 结果
    print(f"\n{'='*60}")
    print(f"📊 最终结果: {len(filtered)} 条")
    print(f"{'='*60}")
    
    for i, p in enumerate(filtered, 1):
        title = p.get('title', 'N/A')
        if len(title) > 70:
            title = title[:70] + "..."
        print(f"\n{i}. {p.get('patent_number')}")
        print(f"   标题: {title}")
        print(f"   匹配: {p.get('matched_keywords', [])}")
    
    print("\n✅ 完成")


if __name__ == "__main__":
    asyncio.run(main())
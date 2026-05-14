#!/usr/bin/env python3
"""
品牌专利搜索 - basic 页面

流程：
1. 在 https://ppubs.uspto.gov/basic/# 输入专利 ID（如 D969457）
2. 直接解析结果表格获取信息
3. 用 config.py 的关键词筛选 Title 字段
"""

import asyncio
import csv
import os
import re
from typing import List, Dict, Set
from playwright.async_api import async_playwright

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CATEGORY_KEYWORDS, CATEGORY_ALIASES


def build_keywords() -> Set[str]:
    keywords = set()
    for kw in CATEGORY_KEYWORDS:
        keywords.add(kw.lower())
    for canonical, aliases in CATEGORY_ALIASES.items():
        keywords.add(canonical.lower())
        for alias in aliases:
            keywords.add(alias.lower())
    return keywords


async def search_by_id(patent_id: str, limit: int = 100) -> List[Dict]:
    """
    在 basic 页面搜索专利 ID，直接解析表格
    """
    print(f"\n{'='*60}")
    print(f"🔍 在 basic 页面搜索 '{patent_id}'...")
    print(f"{'='*60}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            await page.goto("https://ppubs.uspto.gov/basic/#")
            await asyncio.sleep(3)
            print("✅ 页面已加载")
            
            # 找到搜索框
            search_input = await page.wait_for_selector("#quickLookupTextInput", timeout=10000)
            print("✅ 找到搜索框")
            
            # 清理 ID
            clean_id = patent_id.strip()
            if clean_id.startswith("US"):
                parts = clean_id.split()
                if len(parts) >= 2:
                    clean_id = parts[1]
            
            await search_input.fill(clean_id)
            print(f"📝 已输入: {clean_id}")
            
            await asyncio.sleep(0.5)
            
            # 点击搜索
            search_btn = await page.wait_for_selector("#quickLookupSearchBtn", timeout=5000)
            await search_btn.click()
            print("✅ 点击搜索")
            
            # 等待结果表格加载
            await asyncio.sleep(5)
            print("✅ 等待结果...")
            
            # 解析表格
            patents = await parse_results_table(page, limit)
            return patents
        finally:
            await browser.close()


async def parse_results_table(page, limit: int) -> List[Dict]:
    """解析结果表格"""
    patents = []
    
    try:
        # 等待表格加载
        table = await page.wait_for_selector("#searchResults", timeout=10000)
        
        # 获取所有行
        rows = await page.query_selector_all("#searchResults tbody tr")
        print(f"📋 找到 {len(rows)} 条结果")
        
        for i, row in enumerate(rows[:limit]):
            cells = await row.query_selector_all("td")
            if len(cells) >= 6:
                # 提取各列数据
                result_num = await cells[0].inner_text()
                doc_num = await cells[1].inner_text()
                display_link = await cells[2].inner_text()  # Preview, PDF, Text 链接
                title = await cells[3].inner_text()
                inventor = await cells[4].inner_text()
                pub_date = await cells[5].inner_text()
                
                # 清理文档号
                doc_num = doc_num.strip().replace('US-', 'US ')
                
                patents.append({
                    'patent_number': doc_num,
                    'title': title.strip(),
                    'inventor': inventor.strip(),
                    'date_published': pub_date.strip(),
                })
                print(f"  {i+1}. {doc_num} - {title.strip()}")
        
    except Exception as e:
        print(f"⚠️ 解析表格失败: {e}")
        
        # 保存截图
        await page.screenshot(path="debug_table.png")
        print("💾 已保存截图: debug_table.png")
    
    return patents


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
    patent_id = "D969457"
    
    print("="*60)
    print(f"测试 basic 页面搜索: {patent_id}")
    print("="*60)
    
    patents = await search_by_id(patent_id, limit=50)
    print(f"\n📋 获取到 {len(patents)} 条专利")
    
    if not patents:
        print("❌ 未获取到专利")
        return
    
    filtered = filter_by_title(patents)
    
    print(f"\n{'='*60}")
    print(f"📊 最终结果: {len(filtered)} 条")
    print(f"{'='*60}")
    
    for i, p in enumerate(filtered, 1):
        print(f"\n{i}. {p.get('patent_number')}")
        print(f"   标题: {p.get('title', 'N/A')}")
        print(f"   发明人: {p.get('inventor', 'N/A')}")
        print(f"   匹配: {p.get('matched_keywords', [])}")
    
    print("\n✅ 完成")


if __name__ == "__main__":
    asyncio.run(main())
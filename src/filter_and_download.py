#!/usr/bin/env python3
"""
筛选 CSV 文件中的专利并获取 PDF 截图

流程：
1. 读取已有 CSV 文件
2. 用 config.py 关键词筛选 Title
3. 访问 basic 页面搜索每个专利 ID，提取 PDF 链接
4. 下载 PDF 并用 PyMuPDF 截图
"""

import asyncio
import csv
import os
import json
import time
from typing import List, Dict, Set
from playwright.async_api import async_playwright

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CATEGORY_KEYWORDS, CATEGORY_ALIASES, SCREENSHOT_OUTPUT_DIR

# PDF 截图
PYMUPDF_AVAILABLE = False
try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    print("⚠️ PyMuPDF 未安装，将使用备用方案")

PIL_AVAILABLE = False
try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    print("⚠️ Pillow 未安装")


def build_keywords() -> Set[str]:
    keywords = set()
    for kw in CATEGORY_KEYWORDS:
        keywords.add(kw.lower())
    for canonical, aliases in CATEGORY_ALIASES.items():
        keywords.add(canonical.lower())
        for alias in aliases:
            keywords.add(alias.lower())
    return keywords


def filter_patents_from_csv(csv_file: str) -> List[Dict]:
    """从 CSV 筛选专利"""
    print(f"\n{'='*60}")
    print(f"🔍 读取并筛选 CSV 文件...")
    print(f"{'='*60}")
    
    keywords = build_keywords()
    print(f"📋 关键词数量: {len(keywords)}")
    
    patents = []
    filtered = []
    
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            patents.append({
                'patent_number': row.get('Document ID', ''),
                'title': row.get('Title', ''),
                'assignee': row.get('Assignee', ''),
                'inventor': row.get('Inventor', ''),
                'date_published': row.get('Date Published', ''),
            })
    
    print(f"📋 CSV 共有 {len(patents)} 条专利")
    
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


def get_clean_id(pub_num: str) -> str:
    """提取纯数字 ID（如 US D969457 S -> D969457）"""
    clean_id = pub_num.strip()
    if 'US' in clean_id:
        parts = clean_id.split()
        if len(parts) >= 2:
            clean_id = parts[1]
    return clean_id


async def get_pdf_link_from_basic_page(page, patent_id: str) -> str:
    """访问 basic 页面获取 PDF 链接"""
    try:
        clean_id = get_clean_id(patent_id)
        
        await page.goto("https://ppubs.uspto.gov/basic/#", timeout=30000)
        await asyncio.sleep(2)
        
        search_input = await page.query_selector("#quickLookupTextInput")
        if search_input:
            await search_input.fill(clean_id)
            await asyncio.sleep(0.5)
            
            search_btn = await page.query_selector("#quickLookupSearchBtn")
            if search_btn:
                await search_btn.click()
                await asyncio.sleep(3)
        
        pdf_link = None
        links = await page.query_selector_all("a[href*='downloadPdf']")
        for link in links:
            href = await link.get_attribute("href")
            if href and 'downloadPdf' in href:
                pdf_link = href
                break
        
        return pdf_link
        
    except Exception as e:
        print(f"  ⚠️ 获取 PDF 链接失败: {e}")
        return None


async def download_pdf(url: str, save_path: str) -> bool:
    """下载 PDF 文件"""
    import requests
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200 and len(response.content) > 1000:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"  ⚠️ PDF 下载失败: {e}")
    return False


def screenshot_pdf_with_pymupdf(pdf_path: str, output_path: str) -> bool:
    """用 PyMuPDF 截取 PDF 第一页"""
    if not PYMUPDF_AVAILABLE:
        print("  ⚠️ PyMuPDF 未安装")
        return False
    
    try:
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            return False
        
        page = doc[0]
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        pix.save(output_path)
        doc.close()
        return True
    except Exception as e:
        print(f"  ⚠️ PyMuPDF 截图失败: {e}")
        return False


def create_placeholder_screenshot(output_path: str, patent_number: str, title: str = "") -> bool:
    """创建占位截图"""
    if not PIL_AVAILABLE:
        return False
    
    try:
        img = Image.new('RGB', (800, 1000), color='white')
        draw = ImageDraw.Draw(img)
        draw.rectangle([(10, 10), (790, 990)], outline='black', width=2)
        draw.text((50, 50), f"Patent: {patent_number}", fill='black')
        if title:
            draw.text((50, 100), f"Title: {title[:80]}", fill='black')
        draw.text((50, 150), "PDF not available", fill='red')
        img.save(output_path)
        return True
    except:
        return False


async def process_patents(patents: List[Dict], output_dir: str):
    """处理每个专利"""
    print(f"\n{'='*60}")
    print(f"🔍 获取 PDF 链接 → 下载 → 截图...")
    print(f"{'='*60}")
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "pdfs"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "screenshots"), exist_ok=True)
    os.makedirs(SCREENSHOT_OUTPUT_DIR, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        results = []
        total = len(patents)
        
        for i, patent in enumerate(patents, 1):
            pub_num = patent.get('patent_number', '')
            if not pub_num:
                continue
            
            print(f"\n[{i}/{total}] 处理 {pub_num}...")
            clean_id = get_clean_id(pub_num)
            
            pdf_path = os.path.join(output_dir, "pdfs", f"{clean_id}.pdf")
            screenshot_path = os.path.join(SCREENSHOT_OUTPUT_DIR, f"{clean_id}_page1.png")
            
            try:
                # 1. 获取 PDF 链接
                print(f"  🔗 获取 PDF 链接...")
                pdf_url = await get_pdf_link_from_basic_page(page, pub_num)
                
                if pdf_url:
                    print(f"  ✅ 找到 PDF 链接")
                    
                    # 2. 下载 PDF
                    print(f"  📥 下载 PDF...")
                    pdf_ok = await download_pdf(pdf_url, pdf_path)
                    
                    if pdf_ok:
                        print(f"  ✅ PDF 已保存")
                        
                        # 3. PyMuPDF 截图
                        print(f"  📸 PyMuPDF 截图...")
                        ss_ok = screenshot_pdf_with_pymupdf(pdf_path, screenshot_path)
                        
                        if ss_ok:
                            print(f"  ✅ 截图已保存")
                            results.append({
                                **patent,
                                'pdf_path': pdf_path,
                                'screenshot_path': screenshot_path,
                            })
                        else:
                            # 创建占位图
                            create_placeholder_screenshot(screenshot_path, clean_id, patent.get('title', ''))
                            results.append({**patent, 'pdf_path': pdf_path, 'screenshot_path': screenshot_path})
                    else:
                        results.append({**patent, 'pdf_error': True})
                else:
                    print(f"  ⚠️ 未找到 PDF 链接")
                    results.append({**patent, 'link_error': True})
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"  ⚠️ 错误: {str(e)[:50]}")
                results.append({**patent, 'error': str(e)})
        
        await browser.close()
        
        # 保存结果
        result_file = os.path.join(output_dir, "filtered_patents.json")
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 结果已保存: {result_file}")
        
        return results


async def main():
    csv_file = "downloads/SearchResults20260515001627.csv"
    output_dir = "output"
    
    print("="*60)
    print("筛选 CSV 专利 → 获取 PDF 链接 → 下载 PDF → PyMuPDF 截图")
    print("="*60)
    print(f"PyMuPDF 可用: {PYMUPDF_AVAILABLE}")
    
    filtered = filter_patents_from_csv(csv_file)
    
    if not filtered:
        print("❌ 没有匹配的专利")
        return
    
    results = await process_patents(filtered, output_dir)
    
    success = sum(1 for r in results if not r.get('pdf_error') and not r.get('error') and not r.get('link_error'))
    
    print(f"\n{'='*60}")
    print(f"📊 处理完成: {success}/{len(results)} 条成功")
    print(f"{'='*60}")
    
    for i, p in enumerate(results[:10], 1):
        ok = not p.get('pdf_error') and not p.get('error')
        status = "✅" if ok else "❌"
        print(f"\n{i}. {status} {p.get('patent_number')}")
        print(f"   标题: {p.get('title', 'N/A')[:60]}...")
        print(f"   匹配: {p.get('matched_keywords', [])}")
    
    print(f"\n📁 输出目录: {output_dir}")
    print("\n✅ 完成")


if __name__ == "__main__":
    asyncio.run(main())
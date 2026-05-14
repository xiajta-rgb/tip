#!/usr/bin/env python3
"""
完整专利爬取流程

流程：
1. 读取 CSV 文件
2. 只保留 D 开头的外观设计专利
3. 用 config.py 关键词筛选 Title
4. 访问 basic 页面获取 PDF 链接
5. 下载 PDF
6. PyMuPDF 截图
7. 生成报告
"""

import asyncio
import csv
import json
import os
from datetime import datetime
from typing import List, Dict, Set
from playwright.async_api import async_playwright

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CATEGORY_KEYWORDS, CATEGORY_ALIASES, SCREENSHOT_OUTPUT_DIR, BASE_OUTPUT_DIR

PYMUPDF_AVAILABLE = False
try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    print("⚠️ PyMuPDF 未安装")

PIL_AVAILABLE = False
try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    pass


def build_keywords() -> Set[str]:
    keywords = set()
    for kw in CATEGORY_KEYWORDS:
        keywords.add(kw.lower())
    for canonical, aliases in CATEGORY_ALIASES.items():
        keywords.add(canonical.lower())
        for alias in aliases:
            keywords.add(alias.lower())
    return keywords


def is_design_patent(doc_id: str) -> bool:
    """检查是否是外观设计专利（D开头）"""
    clean = doc_id.strip().upper()
    if clean.startswith('US'):
        parts = clean.split()
        if len(parts) >= 2:
            return parts[1].startswith('D')
        return False
    return clean.startswith('D')


def get_clean_id(pub_num: str) -> str:
    """提取纯数字 ID"""
    clean_id = pub_num.strip()
    if 'US' in clean_id:
        parts = clean_id.split()
        if len(parts) >= 2:
            clean_id = parts[1]
    return clean_id


def update_frontend_file(results: List[Dict], output_dir: str):
    """更新前端文件（实时）"""
    report = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_count': len(results),
        'patents': results
    }
    
    classified_path = os.path.join(output_dir, "patent_report_classified.json")
    with open(classified_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"  💾 前端文件已更新: {len(results)} 条")


def load_and_filter_csv(csv_file: str) -> List[Dict]:
    """加载 CSV 并筛选"""
    keywords = build_keywords()
    print(f"📋 关键词数量: {len(keywords)}")
    
    patents = []
    filtered = []
    
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc_id = row.get('Document ID', '')
            
            if not is_design_patent(doc_id):
                continue
            
            title = row.get('Title', '').lower()
            
            matched = []
            for kw in keywords:
                if kw in title:
                    matched.append(kw)
            
            patent = {
                'patent_number': doc_id,
                'patent_number_clean': get_clean_id(doc_id),
                'title': row.get('Title', ''),
                'type': 'design patent',
                'abstract': row.get('Title', ''),
                'publication_date': row.get('Date Published', ''),
                'assignee': row.get('Assignee', ''),
                'inventor': row.get('Inventor', ''),
                'matched_keywords': matched,
            }
            
            patents.append(patent)
            
            if matched:
                filtered.append(patent)
                print(f"  ✅ {doc_id}: {matched[:3]}")
            else:
                print(f"  ⏭️ {doc_id}: 未匹配")
    
    return filtered


async def get_pdf_link(page, patent_id: str) -> str:
    """获取 PDF 链接"""
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
        
        links = await page.query_selector_all("a[href*='downloadPdf']")
        for link in links:
            href = await link.get_attribute("href")
            if href and 'downloadPdf' in href:
                return href
        return None
    except:
        return None


async def download_pdf(url: str, save_path: str) -> bool:
    """下载 PDF"""
    import requests
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200 and len(response.content) > 1000:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
    except:
        return False


def screenshot_pdf_pymupdf(pdf_path: str, output_path: str) -> bool:
    """PyMuPDF 截图"""
    if not PYMUPDF_AVAILABLE:
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
    except:
        return False


async def process_patents(patents: List[Dict], output_dir: str):
    """处理专利，实时更新前端文件"""
    print(f"\n{'='*60}")
    print(f"🔍 开始处理 {len(patents)} 个专利...")
    print(f"{'='*60}")
    
    os.makedirs(output_dir, exist_ok=True)
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
            
            print(f"\n[{i}/{total}] {pub_num}...")
            clean_id = patent.get('patent_number_clean', get_clean_id(pub_num))
            screenshot_path = os.path.join(SCREENSHOT_OUTPUT_DIR, f"{clean_id}_page1.png")
            
            print(f"  🔗 获取 PDF 链接...")
            pdf_url = await get_pdf_link(page, pub_num)
            
            if pdf_url:
                print(f"  ✅ 找到 PDF 链接")
                
                print(f"  📥 下载 PDF...")
                pdf_path = os.path.join(output_dir, "pdfs", f"{clean_id}.pdf")
                os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
                
                if await download_pdf(pdf_url, pdf_path):
                    print(f"  ✅ PDF 已保存")
                    
                    print(f"  📸 PyMuPDF 截图...")
                    if screenshot_pdf_pymupdf(pdf_path, screenshot_path):
                        print(f"  ✅ 截图已保存")
                    
                    results.append({
                        **patent,
                        'pdf_path': pdf_path,
                        'screenshot_path': screenshot_path,
                        'link': f"https://patents.google.com/patent/{clean_id}/en",
                    })
                else:
                    results.append({**patent, 'pdf_error': True})
            else:
                print(f"  ⚠️ 未找到 PDF 链接")
                results.append({**patent, 'link_error': True})
            
            await asyncio.sleep(1)
            
            # 每处理 1 个专利就更新一次前端文件
            update_frontend_file(results, output_dir)
        
        await browser.close()
        return results


def save_reports(results: List[Dict], output_dir: str):
    """保存报告"""
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_path = os.path.join(output_dir, f"patent_report_{timestamp}.json")
    
    report = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_count': len(results),
        'patents': results
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    classified_path = os.path.join(output_dir, "patent_report_classified.json")
    with open(classified_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    latest_path = os.path.join(output_dir, "patent_report_latest.json")
    with open(latest_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 报告已保存: {json_path}")


async def main():
    csv_file = "downloads/SearchResults20260515001627.csv"
    output_dir = BASE_OUTPUT_DIR
    
    print("="*60)
    print("完整专利爬取流程")
    print("="*60)
    print(f"PyMuPDF: {PYMUPDF_AVAILABLE}")
    
    filtered = load_and_filter_csv(csv_file)
    print(f"\n✅ 筛选结果: {len(filtered)} 个外观设计专利")
    
    if not filtered:
        print("❌ 没有匹配的专利")
        return
    
    results = await process_patents(filtered, output_dir)
    save_reports(results, output_dir)
    
    success = len([r for r in results if not r.get('pdf_error') and not r.get('link_error')])
    
    print(f"\n{'='*60}")
    print(f"📊 完成: {success}/{len(results)} 个专利成功")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
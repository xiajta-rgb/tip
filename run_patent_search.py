#!/usr/bin/env python3
"""
专利爬取主入口

工作流程:
1. 品牌关键词搜索(USPTO pubwebapp) -> CSV导出
2. 标题关键词筛选
3. USPTO basic获取详情+PDF+截图
4. 增量追加到 patent_report_latest.json
"""

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime
from typing import List, Dict, Set, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    BASE_OUTPUT_DIR,
    PDF_OUTPUT_DIR,
    SCREENSHOT_OUTPUT_DIR,
    CATEGORY_KEYWORDS,
    CATEGORY_ALIASES,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
)
from src.brand_search_async import BrandPatentSearcher

try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class PatentCrawler:
    """专利爬取器"""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.brand_searcher = BrandPatentSearcher(headless=headless)
        self.keyword_set = self._build_keyword_set()
        self.session = self._create_session()

    def _create_session(self):
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        retry_strategy = Retry(total=MAX_RETRIES, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _build_keyword_set(self) -> Set[str]:
        keywords = set(CATEGORY_KEYWORDS)
        for canonical, aliases in CATEGORY_ALIASES.items():
            keywords.add(canonical)
            keywords.update(aliases)
        return {kw.lower() for kw in keywords}

    def _match_title(self, title: str) -> List[str]:
        title_lower = title.lower()
        return [kw for kw in self.keyword_set if kw in title_lower]

    def get_clean_id(self, pub_num: str) -> str:
        clean_id = pub_num.strip()
        if 'US' in clean_id:
            parts = clean_id.split()
            if len(parts) >= 2:
                clean_id = parts[1]
        return clean_id

    async def crawl_brand(self, brand: str, limit: int = 50) -> List[Dict]:
        """爬取品牌专利"""
        print(f"\n{'='*60}")
        print(f"🔍 开始爬取品牌: {brand}")
        print(f"{'='*60}")

        patents = await self.brand_searcher.search_and_export(brand, limit)
        print(f"📋 从 USPTO 导出了 {len(patents)} 条专利记录")

        filtered = []
        for p in patents:
            matched = self._match_title(p.get('title', ''))
            if matched:
                p['matched_keywords'] = matched
                filtered.append(p)
                print(f"  ✅ {p['patent_number']}: {p['title'][:50]} [{', '.join(matched)}]")

        print(f"\n📊 筛选结果: {len(filtered)}/{len(patents)} 条专利符合条件")
        return filtered

    async def get_pdf_link_from_basic_page(self, page, patent_id: str) -> Optional[str]:
        """访问 basic 页面获取 PDF 链接"""
        try:
            clean_id = self.get_clean_id(patent_id)
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

    def download_pdf(self, url: str, save_path: str) -> bool:
        try:
            response = self.session.get(url, timeout=60)
            if response.status_code == 200 and len(response.content) > 1000:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception as e:
            print(f"  ⚠️ PDF 下载失败: {e}")
        return False

    def screenshot_pdf(self, pdf_path: str, output_path: str) -> bool:
        if not PYMUPDF_AVAILABLE:
            return self._create_placeholder(output_path, os.path.basename(pdf_path).replace('.pdf', ''))

        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
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
            print(f"  ⚠️ 截图失败: {e}")
            return self._create_placeholder(output_path, os.path.basename(pdf_path).replace('.pdf', ''))

    def _create_placeholder(self, output_path: str, patent_number: str) -> bool:
        if not PIL_AVAILABLE:
            return False
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            img = Image.new('RGB', (800, 1000), color='white')
            draw = ImageDraw.Draw(img)
            draw.rectangle([(10, 10), (790, 990)], outline='black', width=2)
            draw.text((50, 50), f"Patent: {patent_number}", fill='black')
            draw.text((50, 150), "PDF not available", fill='red')
            img.save(output_path)
            return True
        except:
            return False

    async def enrich_patents(self, patents: List[Dict]) -> List[Dict]:
        """获取 PDF 和截图"""
        print(f"\n{'='*60}")
        print(f"📥 获取 PDF 和截图...")
        print(f"{'='*60}")

        os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
        os.makedirs(SCREENSHOT_OUTPUT_DIR, exist_ok=True)

        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()

            results = []
            for i, patent in enumerate(patents, 1):
                pub_num = patent.get('patent_number', '')
                if not pub_num:
                    continue

                print(f"\n[{i}/{len(patents)}] 处理 {pub_num}...")
                clean_id = self.get_clean_id(pub_num)

                pdf_path = os.path.join(PDF_OUTPUT_DIR, f"{clean_id}.pdf")
                screenshot_path = os.path.join(SCREENSHOT_OUTPUT_DIR, f"{clean_id}_page1.png")

                patent['pdf_path'] = pdf_path
                patent['screenshot_path'] = screenshot_path
                patent['link'] = f"https://patents.google.com/patent/{clean_id}/en"
                patent['patent_number_clean'] = clean_id

                try:
                    pdf_url = await self.get_pdf_link_from_basic_page(page, pub_num)
                    if pdf_url and self.download_pdf(pdf_url, pdf_path):
                        print(f"  ✅ PDF 已下载")
                        self.screenshot_pdf(pdf_path, screenshot_path)
                        print(f"  ✅ 截图已生成")
                    else:
                        self._create_placeholder(screenshot_path, clean_id)
                        print(f"  ⚠️ 使用占位图")
                except Exception as e:
                    print(f"  ⚠️ 错误: {str(e)[:50]}")
                    self._create_placeholder(screenshot_path, clean_id)

                results.append(patent)
                await asyncio.sleep(1)

            await browser.close()
        return results

    def load_existing_patents(self) -> Dict:
        latest_file = os.path.join(BASE_OUTPUT_DIR, "patent_report_latest.json")
        if os.path.exists(latest_file):
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"generated_at": "", "total_count": 0, "patents": []}

    def save_report(self, patents: List[Dict], timestamp: str = None) -> str:
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        report = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_count": len(patents),
            "patents": patents
        }

        os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)
        report_file = os.path.join(BASE_OUTPUT_DIR, f"patent_report_{timestamp}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report_file

    def merge_to_latest(self, new_patents: List[Dict]) -> int:
        latest_file = os.path.join(BASE_OUTPUT_DIR, "patent_report_latest.json")
        existing = self.load_existing_patents()
        existing_numbers = {p['patent_number'] for p in existing['patents']}

        added_count = 0
        for patent in new_patents:
            if patent['patent_number'] not in existing_numbers:
                existing['patents'].append(patent)
                added_count += 1

        existing['generated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        existing['total_count'] = len(existing['patents'])

        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

        return added_count


async def main():
    parser = argparse.ArgumentParser(description='专利爬取工具')
    parser.add_argument('--brands', type=str, help='品牌关键词列表，用逗号分隔')
    parser.add_argument('--brand', type=str, help='单个品牌关键词')
    parser.add_argument('--limit', type=int, default=50, help='每个品牌最大搜索数量')
    parser.add_argument('--headless', action='store_true', help='无头模式运行浏览器')
    parser.add_argument('--no-pdf', action='store_true', help='跳过 PDF 下载')

    args = parser.parse_args()

    brands = []
    if args.brands:
        brands = [b.strip() for b in args.brands.split(',')]
    elif args.brand:
        brands = [args.brand]
    else:
        print("请提供品牌关键词: --brands 'NIKE,Adidas' 或 --brand 'NIKE'")
        return

    crawler = PatentCrawler(headless=args.headless)
    all_patents = []

    for brand in brands:
        patents = await crawler.crawl_brand(brand, args.limit)
        all_patents.extend(patents)

    if all_patents and not args.no_pdf:
        all_patents = await crawler.enrich_patents(all_patents)

    if all_patents:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = crawler.save_report(all_patents, timestamp)
        print(f"\n💾 报告已保存: {report_file}")

        added = crawler.merge_to_latest(all_patents)
        print(f"📝 已增量追加 {added} 条专利到 patent_report_latest.json")
    else:
        print("\n⚠️ 没有找到符合条件的专利")


if __name__ == "__main__":
    asyncio.run(main())
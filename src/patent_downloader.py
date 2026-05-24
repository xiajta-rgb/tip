#!/usr/bin/env python3
"""
专利 PDF 下载和截图模块
使用 Playwright 浏览器自动化从 USPTO ppubs 网页直接下载 PDF 和截图

流程：
1. 在 https://ppubs.uspto.gov/pubwebapp/ 搜索专利号
2. 点击搜索结果打开 Document Viewer
3. 切换到 Image view，获取图片 URL 和 requestToken
4. 通过浏览器 fetch 下载每页图片
5. 用 PIL/Pillow 将多页图片合并为 PDF
6. 截取 Document Viewer 区域作为首页截图
"""

import asyncio
import base64
import os
import re
import time
from typing import List, Dict, Optional

from playwright.async_api import async_playwright

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import (
    PDF_OUTPUT_DIR,
    SCREENSHOT_OUTPUT_DIR,
    DOWNLOAD_DELAY,
)


class PatentDownloader:
    """专利下载器 - 使用 Playwright 浏览器自动化"""

    MAX_PAGES = 50

    def __init__(self, headless: bool = True):
        self.headless = headless
        os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
        os.makedirs(SCREENSHOT_OUTPUT_DIR, exist_ok=True)

    def _clean_patent_number(self, patent_number: str) -> str:
        return patent_number.replace('-', '').replace(' ', '')

    def _parse_image_url(self, src: str) -> Optional[Dict]:
        """
        解析 ppubs 图片 URL，提取 base_url 和 requestToken

        URL 格式: /api/image/convert?url=uspat/US/G71/191/D11/00000001.tif&requestToken=xxx
        """
        match = re.match(r'(/api/image/convert\?url=)(.+?)&requestToken=(.+)', src)
        if match:
            return {
                'api_prefix': match.group(1),
                'tif_path': match.group(2),
                'request_token': match.group(3),
            }
        return None

    def _get_page_image_url(self, parsed: Dict, page_num: int) -> str:
        """
        根据第一页的 URL 构造指定页码的图片 URL

        tif_path 格式: uspat/US/G71/191/D11/00000001.tif
        页码在文件名中: 00000001 -> 00000002
        """
        tif_path = parsed['tif_path']
        page_str = f'{page_num:08d}'
        new_tif = re.sub(r'/\d{8}\.tif$', f'/{page_str}.tif', tif_path)
        return f"{parsed['api_prefix']}{new_tif}&requestToken={parsed['request_token']}"

    async def _fetch_image_via_browser(self, page, img_url: str) -> Optional[bytes]:
        """通过浏览器 fetch 下载图片（绕过 CORS 和认证限制）"""
        try:
            data_url = await page.evaluate(f'''async () => {{
                try {{
                    const r = await fetch("{img_url}");
                    if (!r.ok) return null;
                    const blob = await r.blob();
                    const reader = new FileReader();
                    return new Promise(resolve => {{
                        reader.onload = () => resolve(reader.result);
                        reader.readAsDataURL(blob);
                    }});
                }} catch(e) {{
                    return null;
                }}
            }}''')

            if data_url and data_url.startswith('data:'):
                b64_data = data_url.split(',', 1)[1]
                return base64.b64decode(b64_data)
        except Exception as e:
            print(f"    [警告] fetch 图片失败: {str(e)[:60]}")
        return None

    async def _search_patent(self, page, patent_number: str) -> bool:
        """在 ppubs 页面搜索专利号"""
        search_term = patent_number.replace('US ', '').replace(' S', '').strip()
        if not search_term:
            search_term = patent_number

        try:
            trix = await page.wait_for_selector('trix-editor.trix', timeout=15000)
            if not trix:
                print(f"  [失败] 未找到搜索框")
                return False

            await trix.click(force=True)
            await asyncio.sleep(0.5)

            await page.evaluate('''() => {
                const editor = document.querySelector('trix-editor.trix');
                if (editor && editor.editor) {
                    editor.editor.loadHTML('');
                }
            }''')
            await asyncio.sleep(0.5)

            await page.evaluate(f'''() => {{
                const editor = document.querySelector('trix-editor.trix');
                if (editor && editor.editor) {{
                    editor.editor.loadHTML('{search_term}');
                }}
            }}''')
            await asyncio.sleep(0.5)
            await page.keyboard.press('Enter')
            print(f"  [搜索] 已输入: {search_term}")

            try:
                await page.wait_for_selector('.slick-row', timeout=20000)
            except Exception:
                await asyncio.sleep(5)

            slick_rows = await page.query_selector_all('.slick-row')
            if not slick_rows:
                print(f"  [失败] 未找到搜索结果")
                return False

            await slick_rows[0].click(force=True)
            print(f"  [点击] 已点击搜索结果")

            try:
                await page.wait_for_selector('.doc-content, .documentViewer', timeout=15000)
            except Exception:
                pass
            await asyncio.sleep(3)
            return True

        except Exception as e:
            print(f"  [失败] 搜索出错: {str(e)[:80]}")
            return False

    async def _switch_to_image_view(self, page) -> bool:
        """切换到 Image view，带重试逻辑"""
        for attempt in range(3):
            try:
                image_btn = await page.wait_for_selector('button.icon-image', timeout=10000, state='visible')
                if image_btn:
                    is_disabled = await image_btn.is_disabled()
                    if is_disabled:
                        await asyncio.sleep(2)
                        continue
                    await image_btn.click(force=True)
                    await asyncio.sleep(4)
                    img_el = await page.query_selector('img[src*="/api/image/convert"]')
                    if img_el:
                        return True
                    await asyncio.sleep(2)
            except Exception:
                await asyncio.sleep(2)
        return False

    async def _get_total_pages(self, page) -> int:
        """获取专利总页数"""
        try:
            all_pages_el = await page.query_selector('.all-pages')
            if all_pages_el:
                text = await all_pages_el.text_content()
                if text and text.strip().isdigit():
                    return int(text.strip())
        except Exception:
            pass
        return 0

    async def _download_pdf_via_playwright(self, page, patent_number: str) -> Optional[str]:
        """
        通过 Playwright 在 USPTO ppubs 网页下载专利 PDF

        流程：
        1. 搜索专利号
        2. 点击搜索结果
        3. 切换到 Image view
        4. 获取图片 URL 和 requestToken
        5. 通过浏览器 fetch 下载每页图片
        6. 用 PIL 合并为 PDF

        Args:
            page: Playwright page 对象
            patent_number: 专利号

        Returns:
            PDF 文件路径，失败返回 None
        """
        clean_number = self._clean_patent_number(patent_number)
        output_filename = f"{clean_number}.pdf"
        output_path = os.path.join(PDF_OUTPUT_DIR, output_filename)

        if os.path.exists(output_path):
            print(f"  [跳过] PDF 已存在: {output_filename}")
            return output_path

        print(f"  [下载] {patent_number} ...")

        if not await self._search_patent(page, patent_number):
            return None

        if not await self._switch_to_image_view(page):
            print(f"  [失败] 无法切换到 Image view")
            return None

        await asyncio.sleep(3)

        img_el = await page.query_selector('img[src*="/api/image/convert"]')
        if not img_el:
            print(f"  [失败] 未找到专利图片")
            return None

        src = await img_el.get_attribute('src')
        if not src:
            print(f"  [失败] 图片 URL 为空")
            return None

        parsed = self._parse_image_url(src)
        if not parsed:
            print(f"  [失败] 无法解析图片 URL: {src[:80]}")
            return None

        total_pages = await self._get_total_pages(page)
        if total_pages == 0:
            total_pages = 6

        print(f"  [信息] 总页数: {total_pages}, Token: {parsed['request_token'][:20]}...")

        temp_dir = os.path.join(PDF_OUTPUT_DIR, f"_temp_{clean_number}")
        os.makedirs(temp_dir, exist_ok=True)

        image_paths = []
        for pg in range(1, min(total_pages + 1, self.MAX_PAGES + 1)):
            page_url = self._get_page_image_url(parsed, pg)
            img_bytes = await self._fetch_image_via_browser(page, page_url)

            if img_bytes is None:
                if pg == 1:
                    print(f"  [失败] 第 1 页图片下载失败")
                    break
                else:
                    print(f"  [信息] 第 {pg} 页不存在，停止下载")
                    break

            img_path = os.path.join(temp_dir, f"page_{pg:03d}.png")
            with open(img_path, 'wb') as f:
                f.write(img_bytes)
            image_paths.append(img_path)

            if pg % 5 == 0:
                print(f"  [进度] 已下载 {pg}/{total_pages} 页")

            await asyncio.sleep(0.3)

        if not image_paths:
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            return None

        if PIL_AVAILABLE:
            try:
                images = []
                for img_path in image_paths:
                    img = Image.open(img_path)
                    if img.mode == 'RGBA':
                        img = img.convert('RGB')
                    images.append(img)

                if images:
                    images[0].save(output_path, save_all=True, append_images=images[1:])
                    file_size = os.path.getsize(output_path)
                    print(f"  [成功] PDF 下载完成 ({len(images)} 页, {file_size/1024:.1f} KB)")
            except Exception as e:
                print(f"  [失败] 合并 PDF 出错: {e}")
                output_path = None
        else:
            print(f"  [失败] PIL 不可用，无法合并图片为 PDF")
            output_path = None

        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

        return output_path

    async def _screenshot_via_playwright(self, page, patent_number: str) -> Optional[str]:
        """
        通过 Playwright 截取专利首页截图

        Args:
            page: Playwright page 对象
            patent_number: 专利号

        Returns:
            截图文件路径，失败返回 None
        """
        clean_number = self._clean_patent_number(patent_number)
        output_filename = f"{clean_number}_page1.png"
        output_path = os.path.join(SCREENSHOT_OUTPUT_DIR, output_filename)

        if os.path.exists(output_path):
            print(f"  [跳过] 截图已存在: {output_filename}")
            return output_path

        print(f"  [截图] {patent_number} ...")

        try:
            img_el = await page.query_selector('img[src*="/api/image/convert"]')
            if img_el:
                box = await img_el.bounding_box()
                if box:
                    clip = {'x': box['x'], 'y': box['y'], 'width': box['width'], 'height': box['height']}
                    await page.screenshot(path=output_path, clip=clip)
                    print(f"  [成功] 截图已保存(精确裁剪): {output_filename}")
                    return output_path

            canvas = await page.query_selector('canvas')
            if canvas:
                box = await canvas.bounding_box()
                if box:
                    clip = {'x': box['x'], 'y': box['y'], 'width': box['width'], 'height': box['height']}
                    await page.screenshot(path=output_path, clip=clip)
                    print(f"  [成功] 截图已保存(canvas裁剪): {output_filename}")
                    return output_path

            doc_content = await page.query_selector('.doc-content')
            if doc_content:
                box = await doc_content.bounding_box()
                if box:
                    clip = {'x': box['x'], 'y': box['y'], 'width': box['width'], 'height': box['height']}
                    await page.screenshot(path=output_path, clip=clip)
                    print(f"  [成功] 截图已保存(doc-content裁剪): {output_filename}")
                    return output_path

            await page.screenshot(path=output_path, full_page=False)
            print(f"  [成功] 页面截图已保存: {output_filename}")
            return output_path

        except Exception as e:
            err_msg = str(e)[:80]
            print(f"  [失败] 截图出错: {err_msg}")
            return None

    def _extract_screenshot_from_pdf(self, pdf_path: str, patent_number: str) -> Optional[str]:
        """从 PDF 提取首页截图"""
        if not PYMUPDF_AVAILABLE:
            return None

        clean_number = self._clean_patent_number(patent_number)
        output_filename = f"{clean_number}_page1.png"
        output_path = os.path.join(SCREENSHOT_OUTPUT_DIR, output_filename)

        if os.path.exists(output_path):
            return output_path

        try:
            doc = fitz.open(pdf_path)
            if len(doc) == 0:
                return None
            page = doc[0]
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)
            pix.save(output_path)
            doc.close()
            print(f"  [成功] 从 PDF 提取截图: {output_filename}")
            return output_path
        except Exception as e:
            print(f"  [失败] 从 PDF 提取截图失败: {e}")
            return None

    def _create_placeholder_screenshot(self, patent_number: str, title: str = "") -> Optional[str]:
        """创建占位截图"""
        if not PIL_AVAILABLE:
            return None

        from PIL import ImageDraw

        clean_number = self._clean_patent_number(patent_number)
        output_filename = f"{clean_number}_page1.png"
        output_path = os.path.join(SCREENSHOT_OUTPUT_DIR, output_filename)

        if os.path.exists(output_path):
            return output_path

        try:
            img = Image.new('RGB', (800, 1000), color='white')
            draw = ImageDraw.Draw(img)
            draw.rectangle([(10, 10), (790, 990)], outline='black', width=2)
            draw.text((50, 50), f"Patent: {patent_number}", fill='black')
            if title:
                draw.text((50, 100), f"Title: {title[:80]}", fill='black')
            draw.text((50, 150), "Screenshot not available", fill='red')
            img.save(output_path)
            return output_path
        except Exception:
            return None

    async def _download_and_extract_async(self, patents: List[Dict], limit: int = 20) -> List[Dict]:
        """
        批量下载专利 PDF 和截图

        流程：
        1. 启动 Edge 浏览器，打开 ppubs 页面
        2. 对每个专利：
           a. 通过 Playwright 在 ppubs 页面搜索并下载图片
           b. 将图片合并为 PDF
           c. 截取 Document Viewer 区域作为截图
           d. 如果截图失败，尝试从 PDF 提取截图
        3. 关闭浏览器

        Args:
            patents: 专利列表
            limit: 最大下载数量

        Returns:
            更新后的专利列表
        """
        print(f"\n📥 开始下载专利 PDF 和截图（最多 {limit} 篇）...")
        print("="*60)

        results = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(channel='msedge', headless=self.headless)
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()

            try:
                await page.goto('https://ppubs.uspto.gov/pubwebapp/', wait_until='domcontentloaded', timeout=120000)
                await asyncio.sleep(5)
                await page.wait_for_selector('trix-editor.trix', timeout=60000)
                await asyncio.sleep(3)
                print(f"✅ ppubs 页面已加载")

                for i, patent in enumerate(patents[:limit], 1):
                    patent_number = patent['patent_number']
                    print(f"\n[{i}/{min(limit, len(patents))}] {patent_number}")
                    print(f"     {patent.get('title', '')[:60]}")

                    pdf_path = await self._download_pdf_via_playwright(page, patent_number)
                    patent['pdf_path'] = pdf_path or ""

                    if pdf_path:
                        screenshot_path = self._extract_screenshot_from_pdf(pdf_path, patent_number)
                    else:
                        screenshot_path = await self._screenshot_via_playwright(page, patent_number)

                    if not screenshot_path:
                        screenshot_path = self._create_placeholder_screenshot(
                            patent_number, patent.get('title', '')
                        )
                    patent['screenshot_path'] = screenshot_path or ""
                    results.append(patent)

                    if i < limit and i < len(patents):
                        time.sleep(DOWNLOAD_DELAY)

            finally:
                await browser.close()

        downloaded = sum(1 for p in results if p.get('pdf_path'))
        screenshots = sum(1 for p in results if p.get('screenshot_path'))

        print(f"\n{'='*60}")
        print(f"✅ 下载完成: {downloaded}/{len(results)} 篇 PDF")
        print(f"✅ 截图完成: {screenshots}/{len(results)} 张")
        print(f"📁 PDF 目录: {PDF_OUTPUT_DIR}")
        print(f"📁 截图目录: {SCREENSHOT_OUTPUT_DIR}")

        return results

    def download_and_extract(self, patents: List[Dict], limit: int = 20) -> List[Dict]:
        """
        批量下载专利 PDF 和截图（同步接口）

        Args:
            patents: 专利列表
            limit: 最大下载数量

        Returns:
            更新后的专利列表
        """
        return asyncio.run(self._download_and_extract_async(patents, limit))


def main():
    downloader = PatentDownloader(headless=False)
    test_patents = [
        {'patent_number': 'US D1119171 S', 'title': 'Pants'},
    ]
    results = downloader.download_and_extract(test_patents, limit=1)
    for r in results:
        print(f"\nPDF: {r.get('pdf_path', 'N/A')}")
        print(f"截图: {r.get('screenshot_path', 'N/A')}")


if __name__ == "__main__":
    main()

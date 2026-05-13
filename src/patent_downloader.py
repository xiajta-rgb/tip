#!/usr/bin/env python3
"""
专利 PDF 下载和截图模块
支持下载 USPTO 专利 PDF 并提取首页截图
"""

import os
import time
import io
from typing import List, Dict, Optional
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# PDF 处理
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("⚠️ PyMuPDF 未安装，PDF 截图功能将不可用")

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import (
    PDF_OUTPUT_DIR,
    SCREENSHOT_OUTPUT_DIR,
    DOWNLOAD_DELAY,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    USE_PROXY,
    PROXY_URL,
    USPTO_PDF_URL_TEMPLATE,
    GOOGLE_PATENTS_URL_TEMPLATE,
)


class PatentDownloader:
    """专利下载器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })
        
        # 配置重试策略
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 代理设置
        if USE_PROXY:
            self.session.proxies = {
                'http': PROXY_URL,
                'https': PROXY_URL,
            }
        
        # 确保输出目录存在
        os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
        os.makedirs(SCREENSHOT_OUTPUT_DIR, exist_ok=True)
    
    def download_patent_pdf(self, patent_number: str, output_filename: Optional[str] = None) -> Optional[str]:
        """
        下载专利 PDF
        
        Args:
            patent_number: 专利号（如 US12624481B1）
            output_filename: 输出文件名（可选）
            
        Returns:
            下载成功的文件路径，失败返回 None
        """
        # 清理专利号
        clean_number = patent_number.replace('-', '').replace(' ', '')
        
        if not output_filename:
            output_filename = f"{clean_number}.pdf"
        
        output_path = os.path.join(PDF_OUTPUT_DIR, output_filename)
        
        # 检查是否已存在
        if os.path.exists(output_path):
            print(f"  [跳过] PDF 已存在: {output_filename}")
            return output_path
        
        print(f"  [下载] {patent_number} ...")
        
        # 策略1: 从 Google Patents 页面提取 PDF 链接
        pdf_url = self._get_pdf_url_from_google_patents(clean_number)
        
        if pdf_url:
            try:
                print(f"  [尝试] {pdf_url[:70]}...")
                response = self.session.get(
                    pdf_url, 
                    timeout=REQUEST_TIMEOUT,
                    stream=True
                )
                response.raise_for_status()
                
                # 下载文件
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # 验证是否为有效 PDF
                with open(output_path, 'rb') as f:
                    header = f.read(4)
                    if header != b'%PDF':
                        os.remove(output_path)
                        print(f"  [跳过] 下载的内容不是有效 PDF")
                        return None
                
                file_size = os.path.getsize(output_path)
                print(f"  [成功] 下载完成 ({file_size/1024:.1f} KB)")
                return output_path
                
            except Exception as e:
                print(f"  [跳过] {str(e)[:80]}")
                if os.path.exists(output_path):
                    os.remove(output_path)
        
        print(f"  [失败] PDF 下载不可用")
        return None
    
    def _get_pdf_url_from_google_patents(self, patent_number: str) -> Optional[str]:
        """
        从 Google Patents 页面提取 PDF 下载链接
        
        Args:
            patent_number: 清理后的专利号
            
        Returns:
            PDF 下载 URL，失败返回 None
        """
        try:
            # 构建 Google Patents 页面 URL
            page_url = f"https://patents.google.com/patent/{patent_number}/en"
            
            response = self.session.get(page_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # 提取 PDF 链接
            import re
            pdf_urls = re.findall(r'href="([^"]*patentimages[^"]*\.pdf)"', response.text)
            
            if pdf_urls:
                return pdf_urls[0]
            
            return None
            
        except Exception as e:
            print(f"  [警告] 无法从 Google Patents 获取 PDF 链接: {str(e)[:60]}")
            return None
    
    def extract_first_page_screenshot(self, pdf_path: str, patent_number: str) -> Optional[str]:
        """
        提取 PDF 首页截图
        
        Args:
            pdf_path: PDF 文件路径
            patent_number: 专利号（用于生成文件名）
            
        Returns:
            截图文件路径，失败返回 None
        """
        if not PYMUPDF_AVAILABLE:
            print("  [跳过] PyMuPDF 未安装，无法提取截图")
            return self._create_placeholder_screenshot(patent_number)
        
        output_filename = f"{patent_number.replace('-', '')}_page1.png"
        output_path = os.path.join(SCREENSHOT_OUTPUT_DIR, output_filename)
        
        if os.path.exists(output_path):
            print(f"  [跳过] 截图已存在: {output_filename}")
            return output_path
        
        try:
            # 打开 PDF
            doc = fitz.open(pdf_path)
            
            if len(doc) == 0:
                print(f"  [失败] PDF 为空")
                return None
            
            # 获取第一页
            page = doc[0]
            
            # 设置缩放比例（2x 提高清晰度）
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)
            
            # 保存为 PNG
            pix.save(output_path)
            
            doc.close()
            
            print(f"  [成功] 截图已保存: {output_filename}")
            return output_path
            
        except Exception as e:
            print(f"  [失败] 截图提取失败: {e}")
            return None
    
    def _create_placeholder_screenshot(self, patent_number: str, title: str = "") -> str:
        """
        创建占位截图（当 PDF 不可用时）
        
        Args:
            patent_number: 专利号
            title: 专利标题
            
        Returns:
            占位截图路径
        """
        if not PIL_AVAILABLE:
            return ""
        
        output_filename = f"{patent_number.replace('-', '')}_page1.png"
        output_path = os.path.join(SCREENSHOT_OUTPUT_DIR, output_filename)
        
        if os.path.exists(output_path):
            return output_path
        
        try:
            # 创建空白图像
            img = Image.new('RGB', (800, 1000), color='white')
            draw = ImageDraw.Draw(img)
            
            # 绘制边框
            draw.rectangle([(10, 10), (790, 990)], outline='black', width=2)
            
            # 添加文本
            draw.text((50, 50), f"Patent: {patent_number}", fill='black')
            if title:
                draw.text((50, 100), f"Title: {title[:80]}", fill='black')
            draw.text((50, 150), "PDF not available in this environment", fill='red')
            draw.text((50, 200), "Please download from USPTO website", fill='blue')
            
            img.save(output_path)
            return output_path
            
        except Exception as e:
            print(f"  [失败] 创建占位截图失败: {e}")
            return ""
    
    def download_and_extract(self, patents: List[Dict], limit: int = 20) -> List[Dict]:
        """
        批量下载专利并提取截图
        
        Args:
            patents: 专利列表
            limit: 最大下载数量
            
        Returns:
            更新后的专利列表（添加 pdf_path 和 screenshot_path 字段）
        """
        print(f"\n📥 开始下载专利 PDF（最多 {limit} 篇）...")
        print("="*60)
        
        results = []
        
        for i, patent in enumerate(patents[:limit], 1):
            print(f"\n[{i}/{min(limit, len(patents))}] {patent['patent_number']}")
            print(f"     {patent['title'][:60]}...")
            
            # 下载 PDF
            pdf_path = self.download_patent_pdf(patent['patent_number'])
            patent['pdf_path'] = pdf_path or ""
            
            # 提取截图
            if pdf_path:
                screenshot_path = self.extract_first_page_screenshot(
                    pdf_path, 
                    patent['patent_number']
                )
            else:
                # 创建占位截图
                screenshot_path = self._create_placeholder_screenshot(
                    patent['patent_number'],
                    patent.get('title', '')
                )
            
            patent['screenshot_path'] = screenshot_path or ""
            results.append(patent)
            
            # 延迟
            if i < limit and i < len(patents):
                time.sleep(DOWNLOAD_DELAY)
        
        # 统计
        downloaded = sum(1 for p in results if p.get('pdf_path'))
        screenshots = sum(1 for p in results if p.get('screenshot_path'))
        
        print(f"\n{'='*60}")
        print(f"✅ 下载完成: {downloaded}/{len(results)} 篇 PDF")
        print(f"✅ 截图完成: {screenshots}/{len(results)} 张")
        print(f"📁 PDF 目录: {PDF_OUTPUT_DIR}")
        print(f"📁 截图目录: {SCREENSHOT_OUTPUT_DIR}")
        
        return results


def main():
    """测试下载功能"""
    downloader = PatentDownloader()
    
    # 测试下载一篇专利
    test_patent = "US12624481B1"
    pdf_path = downloader.download_patent_pdf(test_patent)
    
    if pdf_path:
        screenshot_path = downloader.extract_first_page_screenshot(pdf_path, test_patent)
        print(f"\nPDF: {pdf_path}")
        print(f"截图: {screenshot_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
USPTO 专利爬虫 - 主入口程序

完整工作流：
1. 检索专利（通过 Google Patents API）
2. 下载 PDF（从 USPTO）
3. 提取首页截图
4. 生成 Excel/JSON 报告

使用方法：
    python main.py --keyword "garment" --limit 20
    python main.py --from-report patent_report.json --download-only
"""

import argparse
import json
import os
import sys
import time

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime
from src.uspto_search import USPTOSearcher
from src.patent_downloader import PatentDownloader
from src.report_generator import ReportGenerator
from src.brand_search import BrandPatentSearcher
from config import DEFAULT_KEYWORDS, GARMENT_KEYWORDS, BRAND_KEYWORDS, SHOE_KEYWORDS


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='USPTO 专利爬虫工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 检索服装相关专利
  python main.py --keyword "garment" --limit 20
  
  # 检索多个关键词
  python main.py --keyword "smart garment" --keyword "wearable sensor" --limit 10
  
  # 搜索品牌专利（浏览器自动化）
  python main.py --brand "Nike" --limit 20
  
  # 搜索多个品牌专利
  python main.py --brand "Nike" --brand "Adidas" --limit 10
  
  # 使用默认品牌列表
  python main.py --use-default-brands --limit 20
  
  # 仅检索，不下载PDF
  python main.py --keyword "garment" --limit 50 --no-download
  
  # 从已有报告下载PDF
  python main.py --from-report patent_report.json --download-only
  
  # 使用默认关键词列表
  python main.py --use-default-keywords --limit 20
        """
    )
    
    # 检索参数
    parser.add_argument(
        '-k', '--keyword',
        action='append',
        help='检索关键词（可多次使用）'
    )
    parser.add_argument(
        '--use-default-keywords',
        action='store_true',
        help='使用默认关键词列表'
    )
    parser.add_argument(
        '--brand',
        action='append',
        help='品牌名称（可多次使用，使用浏览器自动化搜索）'
    )
    parser.add_argument(
        '--use-default-brands',
        action='store_true',
        help='使用默认品牌关键词列表'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        default=True,
        help='浏览器无头模式（默认开启）'
    )
    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='显示浏览器窗口（用于调试）'
    )
    parser.add_argument(
        '-l', '--limit',
        type=int,
        default=20,
        help='每关键词最大结果数（默认: 20）'
    )
    
    # 下载参数
    parser.add_argument(
        '--no-download',
        action='store_true',
        help='不下载PDF'
    )
    parser.add_argument(
        '--download-limit',
        type=int,
        default=20,
        help='最大下载数量（默认: 20）'
    )
    parser.add_argument(
        '--from-report',
        help='从已有报告文件加载数据'
    )
    parser.add_argument(
        '--download-only',
        action='store_true',
        help='仅下载PDF（需配合 --from-report）'
    )
    
    # 输出参数
    parser.add_argument(
        '-o', '--output',
        default='output',
        help='输出目录（默认: output）'
    )
    parser.add_argument(
        '--excel-name',
        default='patent_report.xlsx',
        help='Excel报告文件名'
    )
    parser.add_argument(
        '--json-name',
        default='patent_report.json',
        help='JSON报告文件名'
    )
    parser.add_argument(
        '--include-expired',
        action='store_true',
        help='保留过期/无效专利（默认会排除）'
    )
    parser.add_argument(
        '--include-all-categories',
        action='store_true',
        help='保留所有类别专利，不过滤非服装类（用于品牌搜索）'
    )

    return parser.parse_args()


def search_patents(keywords: list, limit: int) -> list:
    """检索专利"""
    print("\n" + "="*70)
    print("🔍 开始检索专利")
    print("="*70)
    
    searcher = USPTOSearcher()
    
    if len(keywords) == 1:
        patents = searcher.search_by_keyword(keywords[0], limit)
    else:
        patents = searcher.search_multiple_keywords(keywords, limit)
    
    print(f"\n✅ 共检索到 {len(patents)} 条不重复专利")
    return patents


def search_brand_patents(brands: list, limit: int, headless: bool = True) -> list:
    """
    搜索品牌专利（使用浏览器自动化）
    
    搜索流程：
    1. 在 https://ppubs.uspto.gov/pubwebapp/ 搜索品牌词，获取专利 ID
    2. 将获取到的 ID 输入到 https://ppubs.uspto.gov/basic/# 进行筛选
    
    Args:
        brands: 品牌名称列表
        limit: 每品牌最大结果数
        headless: 浏览器无头模式
        
    Returns:
        专利列表
    """
    print("\n" + "="*70)
    print("🏷️ 开始搜索品牌专利（浏览器自动化）")
    print("="*70)
    print(f"📋 品牌列表: {', '.join(brands)}")
    print(f"📋 每品牌限制: {limit} 条")
    print(f"📋 浏览器模式: {'无头' if headless else '可视化'}")
    
    searcher = BrandPatentSearcher(headless=headless)
    all_patents = []
    
    try:
        for brand in brands:
            print(f"\n{'='*60}")
            print(f"🏷️ 搜索品牌: {brand}")
            print(f"{'='*60}")
            
            patents = searcher.search_brand_patents(brand, limit)
            all_patents.extend(patents)
            
            print(f"✅ 品牌 '{brand}' 搜索完成，获取 {len(patents)} 条专利")
            time.sleep(2)  # 品牌间延迟
        
        # 去重
        seen_numbers = set()
        unique_patents = []
        for p in all_patents:
            num = p.get('patent_number', '')
            if num and num not in seen_numbers:
                seen_numbers.add(num)
                unique_patents.append(p)
        
        print(f"\n✅ 共搜索到 {len(unique_patents)} 条不重复品牌专利")
        return unique_patents
        
    except Exception as e:
        print(f"\n❌ 品牌搜索出错: {str(e)}")
        return []


def filter_expired_patents(patents: list) -> list:
    """
    P0 筛选：排除已过期/已放弃/无效的专利
    
    Args:
        patents: 原始专利列表
        
    Returns:
        有效专利列表
    """
    print("\n" + "="*70)
    print("🔎 P0 筛选：排除已过期/已放弃/无效专利")
    print("="*70)
    
    generator = ReportGenerator()
    valid_patents = []
    expired_count = 0
    
    for p in patents:
        is_expired = generator._check_patent_expired(p)
        if is_expired:
            expired_count += 1
            legal_status = p.get('legal_status', '未知')
            expiration_date = p.get('expiration_date', '未知')
            print(f"  [排除] {p['patent_number']} - 状态: {legal_status}, 到期日: {expiration_date}")
        else:
            valid_patents.append(p)
    
    print(f"\n✅ 筛选完成: 排除 {expired_count} 项过期专利，剩余 {len(valid_patents)} 项有效专利")
    return valid_patents


def filter_garment_patents(patents: list) -> list:
    """
    服装行业筛选：仅保留与服装相关的专利，剔除鞋类专利
    
    流程：
    1. 先检查是否为鞋类专利，如果是则剔除
    2. 再检查是否匹配服装关键词
    
    Args:
        patents: 原始专利列表
        
    Returns:
        服装相关专利列表
    """
    print("\n" + "="*70)
    print("👕 服装行业筛选：仅保留服装相关专利（剔除鞋类）")
    print("="*70)
    
    garment_patents = []
    shoe_count = 0
    non_garment_count = 0
    
    for p in patents:
        title = (p.get('title', '') + ' ' + p.get('abstract', '')).lower()
        text = ' '.join([
            p.get('title', ''),
            p.get('abstract', ''),
            p.get('ipc_classification', ''),
            p.get('cpc_classification', ''),
            p.get('assignee', ''),
        ]).lower()
        
        if any(kw.lower() in title for kw in SHOE_KEYWORDS):
            shoe_count += 1
            continue
        
        if any(kw.lower() in text for kw in GARMENT_KEYWORDS):
            garment_patents.append(p)
        else:
            non_garment_count += 1
    
    print(f"\n✅ 筛选完成: 剔除 {shoe_count} 项鞋类专利，排除 {non_garment_count} 项非服装专利，剩余 {len(garment_patents)} 项服装相关专利")
    return garment_patents


def filter_design_patents(patents: list) -> list:
    """
    外观专利筛选：仅保留外观设计专利，排除实用专利
    
    判断规则：
    1. type 字段包含 "外观设计专利"
    2. 专利号以 'US D' 或 'D' 开头（外观设计专利编号特征）
    
    Args:
        patents: 原始专利列表
        
    Returns:
        外观专利列表
    """
    print("\n" + "="*70)
    print("🎨 外观专利筛选：仅保留外观设计专利")
    print("="*70)
    
    design_patents = []
    utility_count = 0
    
    for p in patents:
        patent_type = p.get('type', '')
        patent_number = p.get('patent_number', '')
        
        if patent_type == "外观设计专利" or patent_number.startswith('US D') or patent_number.startswith('D'):
            design_patents.append(p)
        else:
            utility_count += 1
    
    print(f"\n✅ 筛选完成: 排除 {utility_count} 项实用专利，剩余 {len(design_patents)} 项外观专利")
    return design_patents


def download_pdfs(patents: list, limit: int, headless: bool = True) -> list:
    """下载 PDF 并提取截图（Playwright 浏览器自动化）"""
    downloader = PatentDownloader(headless=headless)
    return downloader.download_and_extract(patents, limit)


def generate_reports(patents: list, excel_name: str, json_name: str) -> tuple:
    """生成报告"""
    print("\n" + "="*70)
    print("📊 生成报告")
    print("="*70)
    
    generator = ReportGenerator()
    
    # Excel 报告
    excel_path = generator.generate_excel_report(patents, excel_name)
    
    # JSON 报告
    json_path = generator.generate_json_report(patents, json_name)
    
    # 文本摘要
    summary = generator.generate_summary(patents)
    print("\n" + summary)
    
    return excel_path, json_path


def load_from_report(report_path: str) -> list:
    """从报告文件加载数据"""
    print(f"\n📂 从报告加载: {report_path}")
    
    with open(report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 支持两种格式
    if 'patents' in data:
        patents = data['patents']
    else:
        patents = data
    
    # 转换格式
    results = []
    for p in patents:
        if isinstance(p, dict):
            # 统一字段名
            patent = {
                'patent_number': p.get('patent_number', p.get('number', '')),
                'title': p.get('title', ''),
                'inventor': p.get('inventor', ''),
                'assignee': p.get('assignee', ''),
                'publication_date': p.get('publication_date', ''),
                'filing_date': p.get('filing_date', ''),
                'type': p.get('type', ''),
                'link': p.get('link', p.get('patent_url', '')),
                'pdf_path': p.get('pdf_path', p.get('pdf_local_path', '')),
                'screenshot_path': p.get('screenshot_path', ''),
            }
            results.append(patent)
    
    print(f"✅ 加载了 {len(results)} 条专利数据")
    return results


def main():
    """主程序"""
    args = parse_args()
    
    # 生成时间戳
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 设置输出目录
    os.makedirs(args.output, exist_ok=True)
    
    # 确定关键词
    keywords = []
    brands = []
    
    if args.from_report and args.download_only:
        # 仅从报告下载
        patents = load_from_report(args.from_report)
    else:
        # 需要检索
        if args.use_default_brands or args.brand:
            # 品牌搜索模式
            if args.use_default_brands:
                brands = BRAND_KEYWORDS
            elif args.brand:
                brands = args.brand
            
            print(f"\n📋 品牌搜索模式")
            print(f"📋 品牌列表: {', '.join(brands)}")
            print(f"📋 每品牌限制: {args.limit} 条")
            print(f"📋 爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 确定浏览器模式
            headless = not args.no_headless
            
            # 搜索品牌专利
            patents = search_brand_patents(brands, args.limit, headless)
            
        elif args.use_default_keywords:
            keywords = DEFAULT_KEYWORDS
        elif args.keyword:
            keywords = args.keyword
        else:
            # 默认使用 garment
            keywords = ['garment']
        
        if keywords:
            print(f"\n📋 检索关键词: {', '.join(keywords)}")
            print(f"📋 每关键词限制: {args.limit} 条")
            print(f"📋 爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 检索专利
            patents = search_patents(keywords, args.limit)
    
    if not patents:
        print("\n❌ 未找到任何专利，程序结束")
        return 1
    
    # P0 筛选：排除过期专利（除非指定 --include-expired）
    if not args.include_expired:
        patents = filter_expired_patents(patents)
    else:
        print("\n[WARNING] 已启用保留过期专利模式（--include-expired）")

    if not patents:
        print("\n[WARNING] 所有专利均已过期，程序结束")
        return 1

    # 筛选逻辑
    if not args.include_all_categories:
        # 外观专利筛选：仅保留外观专利，排除实用专利
        patents = filter_design_patents(patents)

        if not patents:
            print("\n[X] 无外观专利，程序结束")
            return 1

    # 服装行业筛选：始终执行，剔除鞋类 + 保留服装相关
    patents = filter_garment_patents(patents)

    if not patents:
        print("\n[WARNING] 无服装相关专利，程序结束")
        return 1
    
    # 下载 PDF（除非禁用）
    download_headless = not args.no_headless
    if not args.no_download and not args.download_only:
        patents = download_pdfs(patents, args.download_limit, headless=download_headless)
    elif args.download_only:
        patents = download_pdfs(patents, args.download_limit, headless=download_headless)
    
    # 生成带时间戳的报告文件名
    base_excel_name = args.excel_name.replace('.xlsx', '')
    base_json_name = args.json_name.replace('.json', '')
    excel_name_with_ts = f"{base_excel_name}_{timestamp}.xlsx"
    json_name_with_ts = f"{base_json_name}_{timestamp}.json"
    
    # 生成报告
    excel_path, json_path = generate_reports(
        patents,
        excel_name_with_ts,
        json_name_with_ts
    )
    
    # 生成最新报告副本（供前端使用）
    latest_json_path = os.path.join(args.output, 'patent_report_latest.json')
    import shutil
    shutil.copy2(json_path, latest_json_path)
    print(f"   最新报告:  {latest_json_path}")
    
    # 输出总结
    print("\n" + "="*70)
    print("✅ 全部完成！")
    print("="*70)
    print(f"\n📁 输出文件:")
    if excel_path:
        print(f"   Excel 报告: {excel_path}")
    if json_path:
        print(f"   JSON 报告:  {json_path}")
    print(f"\n📂 输出目录: {os.path.abspath(args.output)}")
    print(f"   ├── pdfs/        - PDF 文件")
    print(f"   ├── screenshots/ - 首页截图")
    print(f"   └── *.xlsx/json  - 报告文件")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

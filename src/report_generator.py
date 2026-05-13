#!/usr/bin/env python3
"""
报告生成模块
支持生成 Excel 和 JSON 格式的专利报告
"""

import json
import os
from typing import List, Dict
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import (
    REPORT_OUTPUT_DIR,
    RISK_KEYWORDS,
    USPTO_PDF_URL_TEMPLATE,
    GOOGLE_PATENTS_URL_TEMPLATE,
)

# Excel 处理
try:
    import pandas as pd
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils.dataframe import dataframe_to_rows
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("⚠️ pandas/openpyxl 未安装，Excel 报告功能将不可用")


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)
    
    def analyze_risk_keywords(self, title: str) -> str:
        """
        分析标题中的侵权风险关键词
        
        Args:
            title: 专利标题
            
        Returns:
            匹配的风险类别，逗号分隔
        """
        title_lower = title.lower()
        matched_categories = []
        
        for category, keywords in RISK_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    matched_categories.append(category)
                    break
        
        return ", ".join(matched_categories) if matched_categories else "一般"
    
    def generate_pdf_url(self, patent_number: str) -> str:
        """生成 PDF 下载链接"""
        clean_number = patent_number.replace('-', '').replace(' ', '')
        doc_id = clean_number.replace('US', '').replace('B1', '').replace('B2', '').replace('A1', '').replace('A2', '')
        return USPTO_PDF_URL_TEMPLATE.format(doc_id=doc_id)
    
    def generate_google_patents_url(self, patent_number: str) -> str:
        """生成 Google Patents 链接"""
        clean_number = patent_number.replace('-', '').replace(' ', '')
        return GOOGLE_PATENTS_URL_TEMPLATE.format(patent_number=clean_number)
    
    def generate_excel_report(self, patents: List[Dict], filename: str = "patent_report.xlsx") -> str:
        """
        生成 Excel 报告
        
        Args:
            patents: 专利列表
            filename: 输出文件名
            
        Returns:
            生成的文件路径
        """
        if not PANDAS_AVAILABLE:
            print("❌ pandas 未安装，无法生成 Excel 报告")
            return ""
        
        output_path = os.path.join(REPORT_OUTPUT_DIR, filename)
        
        # 准备数据
        crawl_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = []
        for i, p in enumerate(patents, 1):
            data.append({
                '序号': i,
                '专利号': p['patent_number'],
                '专利标题': p['title'],
                '发明人': p.get('inventor', ''),
                '申请人': p.get('assignee', ''),
                '公布日期': p.get('publication_date', ''),
                '申请日期': p.get('filing_date', ''),
                '专利类型': p.get('type', ''),
                'USPTO链接': p.get('link', ''),
                'PDF链接': self.generate_pdf_url(p['patent_number']),
                'GooglePatents链接': self.generate_google_patents_url(p['patent_number']),
                '侵权风险关键词': self.analyze_risk_keywords(p['title']),
                'PDF本地路径': p.get('pdf_path', ''),
                '截图路径': p.get('screenshot_path', ''),
                '爬取时间': crawl_timestamp,
            })
        
        # 创建 DataFrame
        df = pd.DataFrame(data)
        
        # 使用 openpyxl 创建带样式的 Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "专利检索报告"
        
        # 写入数据
        for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
            for c_idx, value in enumerate(row, 1):
                cell = ws.cell(row=r_idx, column=c_idx, value=value)
                
                # 表头样式
                if r_idx == 1:
                    cell.font = Font(bold=True, color="FFFFFF", size=11)
                    cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                else:
                    # 交替行颜色
                    if r_idx % 2 == 0:
                        cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
                    cell.alignment = Alignment(vertical="center", wrap_text=True)
        
        # 设置列宽
        column_widths = {
            'A': 6,   # 序号
            'B': 18,  # 专利号
            'C': 50,  # 专利标题
            'D': 25,  # 发明人
            'E': 25,  # 申请人
            'F': 12,  # 公布日期
            'G': 12,  # 申请日期
            'H': 15,  # 专利类型
            'I': 50,  # USPTO链接
            'J': 60,  # PDF链接
            'K': 50,  # GooglePatents链接
            'L': 30,  # 侵权风险关键词
            'M': 40,  # PDF本地路径
            'N': 40,  # 截图路径
            'O': 20,  # 爬取时间
        }
        
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width
        
        # 冻结首行
        ws.freeze_panes = 'A2'
        
        # 添加筛选
        ws.auto_filter.ref = ws.dimensions
        
        # 保存
        wb.save(output_path)
        
        print(f"✅ Excel 报告已生成: {output_path}")
        return output_path
    
    def generate_json_report(self, patents: List[Dict], filename: str = "patent_report.json") -> str:
        """
        生成 JSON 报告
        
        Args:
            patents: 专利列表
            filename: 输出文件名
            
        Returns:
            生成的文件路径
        """
        output_path = os.path.join(REPORT_OUTPUT_DIR, filename)
        
        # 构建报告结构
        crawl_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'crawl_timestamp': crawl_timestamp,
                'total_patents': len(patents),
                'source': 'USPTO Patent Public Search',
            },
            'patents': []
        }
        
        for p in patents:
            report['patents'].append({
                'patent_number': p['patent_number'],
                'title': p['title'],
                'inventor': p.get('inventor', ''),
                'assignee': p.get('assignee', ''),
                'publication_date': p.get('publication_date', ''),
                'filing_date': p.get('filing_date', ''),
                'type': p.get('type', ''),
                'crawl_timestamp': crawl_timestamp,
                'links': {
                    'uspto': p.get('link', ''),
                    'pdf': self.generate_pdf_url(p['patent_number']),
                    'google_patents': self.generate_google_patents_url(p['patent_number']),
                },
                'risk_analysis': {
                    'keywords': self.analyze_risk_keywords(p['title']),
                },
                'local_files': {
                    'pdf_path': p.get('pdf_path', ''),
                    'screenshot_path': p.get('screenshot_path', ''),
                }
            })
        
        # 保存 JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON 报告已生成: {output_path}")
        return output_path
    
    def generate_summary(self, patents: List[Dict]) -> str:
        """
        生成文本摘要
        
        Args:
            patents: 专利列表
            
        Returns:
            摘要文本
        """
        lines = []
        lines.append("=" * 70)
        lines.append("USPTO 专利检索报告摘要")
        lines.append("=" * 70)
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"专利总数: {len(patents)}")
        lines.append("")
        
        # 统计专利类型
        type_counts = {}
        for p in patents:
            ptype = p.get('type', '未知')
            type_counts[ptype] = type_counts.get(ptype, 0) + 1
        
        lines.append("【专利类型分布】")
        for ptype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {ptype}: {count} 项")
        lines.append("")
        
        # 统计风险关键词
        risk_counts = {}
        for p in patents:
            risks = self.analyze_risk_keywords(p['title'])
            if risks and risks != "一般":
                for risk in risks.split(', '):
                    risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        if risk_counts:
            lines.append("【侵权风险分类】")
            for risk, count in sorted(risk_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                lines.append(f"  {risk}: {count} 项")
            lines.append("")
        
        # 最新专利
        lines.append("【最新 5 项专利】")
        for i, p in enumerate(patents[:5], 1):
            lines.append(f"\n{i}. {p['patent_number']}")
            lines.append(f"   标题: {p['title']}")
            lines.append(f"   发明人: {p.get('inventor', '')}")
            lines.append(f"   日期: {p.get('publication_date', '')}")
        
        lines.append("")
        lines.append("=" * 70)
        
        summary = "\n".join(lines)
        
        # 保存摘要文件
        summary_path = os.path.join(REPORT_OUTPUT_DIR, "summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        return summary


def main():
    """测试报告生成"""
    # 测试数据
    test_patents = [
        {
            'patent_number': 'US12624481B1',
            'title': 'Flame-resistant elastic plaited fabric',
            'inventor': 'Trexler; Donald W. et al.',
            'assignee': 'Test Company',
            'publication_date': '2026-05-12',
            'filing_date': '2024-01-15',
            'type': '实用专利(B1)',
            'link': 'https://ppubs.uspto.gov/pubwebapp/?patentNumber=US12624481B1',
            'pdf_path': '',
            'screenshot_path': '',
        },
        {
            'patent_number': 'US12623068B1',
            'title': 'Wearable neurostimulation system and method',
            'inventor': 'John; Michael Sasha et al.',
            'assignee': 'Medical Corp',
            'publication_date': '2026-05-12',
            'filing_date': '2024-02-20',
            'type': '实用专利(B1)',
            'link': 'https://ppubs.uspto.gov/pubwebapp/?patentNumber=US12623068B1',
            'pdf_path': '',
            'screenshot_path': '',
        },
    ]
    
    generator = ReportGenerator()
    
    # 生成 Excel
    if PANDAS_AVAILABLE:
        generator.generate_excel_report(test_patents, "test_report.xlsx")
    
    # 生成 JSON
    generator.generate_json_report(test_patents, "test_report.json")
    
    # 生成摘要
    summary = generator.generate_summary(test_patents)
    print("\n" + summary)


if __name__ == "__main__":
    main()

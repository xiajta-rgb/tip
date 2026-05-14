#!/usr/bin/env python3
"""
专利报告聚合脚本

功能：
1. 扫描 output 目录下所有 patent_report_*.json 文件
2. 合并所有专利数据并去重（基于专利号）
3. 过滤掉没有摘要的专利（abstract 为空或 "No abstract available"）
4. 生成聚合后的 patent_report_latest.json 供前端使用
"""

import json
import os
import glob
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def load_all_reports():
    """加载所有专利报告文件"""
    reports = []
    pattern = os.path.join(OUTPUT_DIR, "patent_report_*.json")
    
    for filepath in glob.glob(pattern):
        filename = os.path.basename(filepath)
        if filename == "patent_report_latest.json":
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'patents' in data:
                    reports.append({
                        'file': filename,
                        'patents': data['patents'],
                        'count': len(data['patents'])
                    })
                    print(f"✅ 加载 {filename}: {len(data['patents'])} 条专利")
        except Exception as e:
            print(f"❌ 加载 {filename} 失败: {e}")
    
    return reports


def deduplicate_patents(all_patents):
    """去重专利，基于专利号"""
    seen = {}
    for patent in all_patents:
        patent_number = patent.get('patent_number', '')
        if patent_number and patent_number not in seen:
            seen[patent_number] = patent
    
    return list(seen.values())


def filter_patents(patents):
    """过滤掉没有摘要的专利（但外观专利除外）"""
    filtered = []
    skipped = 0
    
    for patent in patents:
        abstract = patent.get('abstract', '').strip()
        patent_type = patent.get('type', '')
        
        # 外观专利通常没有摘要，保留
        if '外观' in patent_type or 'design' in patent_type.lower():
            filtered.append(patent)
            continue
        
        # 对于其他类型专利，过滤掉明确标注为无摘要的
        if abstract.lower() in ['no abstract available', '']:
            skipped += 1
            continue
        
        filtered.append(patent)
    
    print(f"\n📊 过滤统计:")
    print(f"   - 过滤前: {len(patents) + skipped} 条")
    print(f"   - 已过滤: {skipped} 条")
    print(f"   - 过滤后: {len(filtered)} 条")
    
    return filtered


def aggregate_reports():
    """主聚合流程"""
    print("=" * 60)
    print("🔍 专利报告聚合工具")
    print("=" * 60)
    print()
    
    reports = load_all_reports()
    
    if not reports:
        print("\n❌ 未找到任何专利报告文件")
        return
    
    total_files = len(reports)
    total_patents_before = sum(r['count'] for r in reports)
    
    print(f"\n📈 汇总统计:")
    print(f"   - 报告文件数: {total_files}")
    print(f"   - 专利总数（含重复）: {total_patents_before}")
    
    all_patents = []
    for report in reports:
        all_patents.extend(report['patents'])
    
    print(f"\n🔄 开始去重...")
    unique_patents = deduplicate_patents(all_patents)
    print(f"   - 去重后: {len(unique_patents)} 条")
    print(f"   - 重复数: {len(all_patents) - len(unique_patents)} 条")
    
    print(f"\n🔍 开始过滤无摘要专利...")
    filtered_patents = filter_patents(unique_patents)
    
    output_path = os.path.join(OUTPUT_DIR, "patent_report_latest.json")
    
    report_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_files_merged': total_files,
            'total_patents_before_dedup': total_patents_before,
            'total_patents_after_dedup': len(unique_patents),
            'total_patents_after_filter': len(filtered_patents),
            'source': 'Aggregated from multiple patent reports',
        },
        'patents': filtered_patents
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 聚合报告已生成: {output_path}")
    print(f"📊 最终专利数: {len(filtered_patents)} 条")
    print("=" * 60)


if __name__ == "__main__":
    aggregate_reports()

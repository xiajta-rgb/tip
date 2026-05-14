#!/usr/bin/env python3
"""
合并所有专利 JSON 文件并去重

规则：
1. 只保留 D 开头的外观设计专利
2. 合并所有 JSON 并去重（按 patent_number）
3. 生成合并后的 JSON 和 Excel 报告
"""

import json
import os
import glob
from datetime import datetime
from typing import List, Dict, Set

import sys
sys.path.insert(0, os.path.dirname(__file__))


def is_design_patent(patent_number: str) -> bool:
    """检查是否是外观设计专利（D开头）"""
    clean = patent_number.strip().upper()
    if clean.startswith('US'):
        parts = clean.split()
        if len(parts) >= 2:
            return parts[1].startswith('D')
    return clean.startswith('D')


def merge_patents(json_files: List[str]) -> List[Dict]:
    """合并并去重专利"""
    seen = set()
    merged = []
    
    for json_file in json_files:
        if not os.path.exists(json_file):
            continue
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            patents = data.get('patents', []) if isinstance(data, dict) else data
            
            for p in patents:
                pub_num = p.get('patent_number', '')
                if not pub_num:
                    continue
                
                # 只保留 D 开头的外观设计专利
                if not is_design_patent(pub_num):
                    continue
                
                # 去重
                if pub_num not in seen:
                    seen.add(pub_num)
                    merged.append(p)
                    
        except Exception as e:
            print(f"⚠️ 读取 {json_file} 失败: {e}")
    
    return merged


def generate_excel_report(patents: List[Dict], output_path: str):
    """生成 Excel 报告"""
    try:
        import pandas as pd
        
        df = pd.DataFrame(patents)
        
        # 提取需要的列
        columns = ['patent_number', 'title', 'inventor', 'assignee', 
                   'date_published', 'matched_keywords']
        
        # 只保留存在的列
        available_cols = [c for c in columns if c in df.columns]
        if available_cols:
            df = df[available_cols]
        
        df.to_excel(output_path, index=False)
        print(f"✅ Excel 已保存: {output_path}")
        
    except ImportError:
        print("⚠️ pandas 未安装，跳过 Excel 生成")
    except Exception as e:
        print(f"⚠️ Excel 生成失败: {e}")


def generate_json_report(patents: List[Dict], output_path: str):
    """生成 JSON 报告"""
    try:
        report = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_count': len(patents),
            'patents': patents
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON 已保存: {output_path}")
        
    except Exception as e:
        print(f"⚠️ JSON 生成失败: {e}")


def main():
    print("="*60)
    print("合并所有专利 JSON 文件")
    print("="*60)
    
    # 查找所有 JSON 文件
    json_files = glob.glob("output/patent_report_*.json")
    json_files = [f for f in json_files if 'merged' not in f]
    
    print(f"📁 找到 {len(json_files)} 个 JSON 文件")
    for f in json_files:
        print(f"   - {os.path.basename(f)}")
    
    # 合并
    merged = merge_patents(json_files)
    print(f"\n📋 合并后共 {len(merged)} 个外观设计专利（D开头）")
    
    # 保存
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    json_path = os.path.join(output_dir, f"patent_report_merged_{timestamp}.json")
    excel_path = os.path.join(output_dir, f"patent_report_merged_{timestamp}.xlsx")
    
    generate_json_report(merged, json_path)
    generate_excel_report(merged, excel_path)
    
    # 也保存为 latest
    latest_json = os.path.join(output_dir, "patent_report_latest.json")
    generate_json_report(merged, latest_json)
    
    print(f"\n{'='*60}")
    print(f"📊 合并完成！共 {len(merged)} 个外观设计专利")
    print(f"{'='*60}")
    
    # 显示前 10 个
    print("\n前 10 个专利：")
    for i, p in enumerate(merged[:10], 1):
        title = p.get('title', 'N/A')
        if len(title) > 50:
            title = title[:50] + "..."
        print(f"{i}. {p.get('patent_number')}")
        print(f"   {title}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
CSV 批量打标脚本

功能：
1. 读取 USPTO 导出的 CSV
2. 在第一列添加"标签"字段（根据标题关键词自动分类）
3. 在第二列添加"采集"字段（Y/N）
4. 提示用户审查并确认
"""

import csv
import os
import sys
from typing import Dict, List, Optional

LABEL_KEYWORDS = {
    '上装': [
        't-shirt', 'tshirt', 't shirt', 'polo shirt', 'blouse', 'sweater', 'hoodie', 'jersey', 'tunic', 'pullover', 'henley', 'camisole', 'bodice', 'crop top', 'shirt',
        'cardigan', 'vest', 'tank', 'bralette', 'sweatshirt', 'polo', 'henley', 'tank top', 'sleeveless'
    ],
    '下装': [
        'jeans', 'pants', 'shorts', 'short', 'trouser', 'chinos', 'bermuda', 'cargo', 'jogger', 'sweatshort', 'culotte', 'capri', 'palazzo'
    ],
    '套装': [
        'lounge set', 'two-piece', 'co-ord', 'suit', 'ensemble', 'coordinate', 'jumpsuit', 'romper', 'matching set', 'set', 'track suit'
    ],
    '外套': [
        'jacket', 'coat', 'vest', 'parka', 'blazer', 'windbreaker', 'cape', 'cloak', 'anorak', 'raincoat', 'overcoat', 'outerwear', 'parkas', 'fleece', 'softshell', 'bomber', 'puffer', 'gilet', 'wind vest'
    ],
    '连衣裙': [
        'dress', 'gown', 'frock', 'one-piece', 'one piece', 'maxi', 'midi', 'mini dress', 'cocktail dress', 'evening gown', 'sheath', 'wrap dress'
    ],
    '头饰': [
        'hijab', 'scarf', 'bandana', 'wrap', 'sarong', 'kaftan', 'turban', 'headband', 'shawl', 'poncho', 'stole', 'hat', 'cap', 'beanie', 'visor', 'headwear'
    ],
    '面罩': [
        'mask', 'goggle', 'face shield', 'eye protection', 'safety glasses'
    ],
    '腕带': [
        'watch band', 'smart band', 'wearable band', 'strap', 'bracelet'
    ],
    '包袋': [
        'bag', 'backpack', 'handbag', 'tote', 'purse', 'pouch', 'wallet', 'clutch', 'luggage'
    ],
    '服装面料': [
        'textile', 'fabric', 'woven', 'knit', 'nonwoven', 'laminate', 'foam', 'cushion', 'bladders'
    ],
    '可穿戴': [
        'wearable', 'wearable article', 'apparel', 'garment', 'support garment', 'clothing', 'apparel'
    ],
    '智能设备': [
        'smart watch', 'smart band', 'fitness tracker', 'wearable device', 'smart device'
    ],
    '鞋类': [
        'shoe', 'footwear', 'boot', 'sandal', 'slipper', 'sneaker', 'outsole', 'midsole', 'insole', 'athletic shoe', 'loafer', 'moccasin', 'cleat', 'spike'
    ],
}


def auto_label(title: str) -> tuple:
    """
    根据标题自动打标

    Args:
        title: 专利标题

    Returns:
        (标签, 是否采集)
    """
    if not title:
        return ('未知', 'N')

    title_lower = title.lower()

    for label, keywords in LABEL_KEYWORDS.items():
        for kw in keywords:
            if kw in title_lower:
                if label == '鞋类':
                    return ('鞋类', 'N')
                else:
                    return (label, 'Y')

    return ('其他', 'N')


def find_title_column(headers: list) -> int:
    """
    根据表头名称找到 Title 列的索引

    USPTO CSV 可能的 Title 列名：
    - 'Title'
    - 'title'
    - 'TI' (USPTO 常用缩写)
    """
    for i, h in enumerate(headers):
        h_lower = h.lower().strip()
        if h_lower == 'title':
            return i
    return 13  # 默认值


def find_doc_id_column(headers: list) -> int:
    """
    根据表头名称找到 Document ID 列的索引
    """
    for i, h in enumerate(headers):
        h_lower = h.lower().strip()
        if 'document' in h_lower and 'id' in h_lower:
            return i
        if h_lower == 'document id':
            return i
    return 10  # USPTO CSV 默认值


def process_csv(input_path: str, output_path: Optional[str] = None) -> tuple:
    """
    处理 CSV 文件，添加标签和采集列

    Args:
        input_path: 输入 CSV 路径
        output_path: 输出 CSV 路径（默认在文件名后加 _labeled）

    Returns:
        (统计信息 dict, 输出文件路径)
    """
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_labeled.csv"

    stats = {
        'total': 0,
        'labels': {},
        'collect_y': 0,
        'collect_n': 0,
    }

    rows_to_write = []
    title_col_idx = 13  # 默认值
    doc_id_col_idx = 10  # 默认值

    with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        for row_idx, row in enumerate(reader):
            if row_idx == 0:
                title_col_idx = find_title_column(row)
                doc_id_col_idx = find_doc_id_column(row)
                new_headers = ['标签', '采集'] + row
                rows_to_write.append(new_headers)
            else:
                stats['total'] += 1

                doc_id = ''
                if len(row) > doc_id_col_idx:
                    doc_id = row[doc_id_col_idx].strip() if row[doc_id_col_idx] else ''

                is_design_patent = doc_id.startswith('US D') or doc_id.startswith('D')

                title = ''
                if len(row) > title_col_idx:
                    title = row[title_col_idx].strip() if row[title_col_idx] else ''

                label, collect = auto_label(title)

                if not is_design_patent:
                    label = '实用专利'
                    collect = 'N'

                stats['labels'][label] = stats['labels'].get(label, 0) + 1
                if collect == 'Y':
                    stats['collect_y'] += 1
                else:
                    stats['collect_n'] += 1

                new_row = [label, collect] + row
                rows_to_write.append(new_row)

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows_to_write)

    return stats, output_path


def prompt_user_review(output_path: str) -> bool:
    """
    提示用户审查 CSV 并确认

    Args:
        output_path: CSV 文件路径

    Returns:
        True: 用户确认继续
        False: 用户取消
    """
    print(f"\n{'='*60}")
    print("📁 CSV 打标完成！")
    print(f"{'='*60}")
    print(f"\n文件: {output_path}")
    print("\n标签分布:")
    stats, _ = process_csv.__self__ if False else (None, output_path)

    with open(output_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        label_counts = {}
        for row in reader:
            label = row.get('标签', '未知')
            label_counts[label] = label_counts.get(label, 0) + 1

    for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {label}: {count} 条")

    print(f"\n⚠️ 请打开 CSV 文件进行审查维护！")
    print("   - 检查标签分类是否正确")
    print("   - 修改'采集'列（Y/N）决定是否采集")
    print("   - 确认后输入 Y 继续，输入 N 取消...")

    while True:
        user_input = input("\n> ").strip().upper()
        if user_input == 'Y':
            return True
        elif user_input == 'N':
            return False
        else:
            print("请输入 Y 或 N")


def main():
    if len(sys.argv) < 2:
        print("用法: python csv_labeler.py <CSV文件路径>")
        print("示例: python csv_labeler.py downloads/NIKE.csv")
        sys.exit(1)

    input_path = sys.argv[1]
    if not os.path.exists(input_path):
        print(f"❌ 文件不存在: {input_path}")
        sys.exit(1)

    stats, output_path = process_csv(input_path)

    print(f"\n{'='*60}")
    print("📋 CSV 批量打标完成！")
    print(f"{'='*60}")
    print(f"\n输入文件: {input_path}")
    print(f"输出文件: {output_path}")
    print(f"\n总计: {stats['total']} 条专利")
    print("\n标签分布:")
    for label, count in sorted(stats['labels'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {label}: {count} 条")

    print(f"\n采集标记:")
    print(f"  ✅ 待采集 (Y): {stats['collect_y']} 条")
    print(f"  ⏭️  跳过 (N): {stats['collect_n']} 条")

    print(f"\n{'='*60}")
    print("⚠️ 请打开 CSV 文件进行审查维护！")
    print("   - 检查标签分类是否正确")
    print("   - 修改'采集'列（Y/N）决定是否采集")
    print("   - 确认后输入 Y 继续，输入 N 取消...")
    print(f"{'='*60}")

    while True:
        user_input = input("\n> ").strip().upper()
        if user_input == 'Y':
            print("✅ 用户确认，继续后续步骤...")
            return 0
        elif user_input == 'N':
            print("❌ 用户取消")
            return 1
        else:
            print("请输入 Y 或 N")


if __name__ == "__main__":
    sys.exit(main())
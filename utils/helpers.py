#!/usr/bin/env python3
"""
工具函数集合
"""

import os
import re
from typing import Optional
from urllib.parse import urlparse


def clean_patent_number(patent_number: str) -> str:
    """
    清理专利号格式
    
    Args:
        patent_number: 原始专利号（如 US-12624481-B1）
        
    Returns:
        清理后的专利号（如 US12624481B1）
    """
    return patent_number.replace('-', '').replace(' ', '')


def extract_doc_id(patent_number: str) -> str:
    """
    从专利号提取文档 ID（用于 USPTO PDF 链接）
    
    Args:
        patent_number: 专利号
        
    Returns:
        文档 ID（数字部分）
    """
    clean = clean_patent_number(patent_number)
    # 移除前缀和类型后缀
    doc_id = re.sub(r'^US', '', clean)
    doc_id = re.sub(r'(B1|B2|A1|A2)$', '', doc_id)
    return doc_id


def is_valid_patent_number(patent_number: str) -> bool:
    """
    验证专利号格式是否有效
    
    Args:
        patent_number: 专利号
        
    Returns:
        是否有效
    """
    pattern = r'^US-?\d{5,12}-?[A-Z]\d?$'
    return bool(re.match(pattern, patent_number, re.IGNORECASE))


def get_file_size_readable(file_path: str) -> str:
    """
    获取可读的文件大小
    
    Args:
        file_path: 文件路径
        
    Returns:
        可读的大小（如 "1.5 MB"）
    """
    if not os.path.exists(file_path):
        return "0 B"
    
    size = os.path.getsize(file_path)
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    
    return f"{size:.1f} TB"


def sanitize_filename(filename: str) -> str:
    """
    清理文件名中的非法字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        安全的文件名
    """
    # Windows 非法字符
    illegal_chars = '<>:"/\\|?*'
    
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    
    # 移除控制字符
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # 限制长度
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200 - len(ext)] + ext
    
    return filename.strip()


def format_date(date_str: str) -> str:
    """
    格式化日期字符串
    
    Args:
        date_str: 原始日期（如 2026-05-12）
        
    Returns:
        格式化后的日期
    """
    if not date_str:
        return ""
    
    # 尝试多种格式
    formats = ['%Y-%m-%d', '%Y%m%d', '%m/%d/%Y', '%d/%m/%Y']
    
    for fmt in formats:
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return date_str


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 后缀
        
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def count_keywords(text: str, keywords: list) -> dict:
    """
    统计文本中关键词出现次数
    
    Args:
        text: 文本
        keywords: 关键词列表
        
    Returns:
        关键词计数字典
    """
    text_lower = text.lower()
    counts = {}
    
    for keyword in keywords:
        count = text_lower.count(keyword.lower())
        if count > 0:
            counts[keyword] = count
    
    return counts


def ensure_dir(directory: str) -> str:
    """
    确保目录存在
    
    Args:
        directory: 目录路径
        
    Returns:
        目录路径
    """
    os.makedirs(directory, exist_ok=True)
    return directory


def get_file_extension(url: str) -> str:
    """
    从 URL 获取文件扩展名
    
    Args:
        url: URL
        
    Returns:
        扩展名（如 .pdf）
    """
    parsed = urlparse(url)
    path = parsed.path
    
    if '.' in path:
        return os.path.splitext(path)[1].lower()
    
    return ''


def merge_patent_data(existing: list, new: list, key: str = 'patent_number') -> list:
    """
    合并专利数据，去重
    
    Args:
        existing: 已有数据
        new: 新数据
        key: 去重字段
        
    Returns:
        合并后的数据
    """
    seen = {item[key] for item in existing}
    merged = existing.copy()
    
    for item in new:
        if item[key] not in seen:
            seen.add(item[key])
            merged.append(item)
    
    return merged


# 专利类型映射
PATENT_TYPE_MAP = {
    'B1': '实用专利（首次授权）',
    'B2': '实用专利（再版/续展）',
    'A1': '专利申请公开',
    'A2': '专利申请公开（修正）',
    'S': '外观设计专利',
    'D': '外观设计专利',
    'E': '再审查证书',
    'H': '依法登记发明',
}


def get_patent_type_description(type_code: str) -> str:
    """
    获取专利类型描述
    
    Args:
        type_code: 类型代码（如 B1, B2）
        
    Returns:
        类型描述
    """
    return PATENT_TYPE_MAP.get(type_code.upper(), '未知类型')


def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度（简单实现）
    
    Args:
        text1: 文本1
        text2: 文本2
        
    Returns:
        相似度（0-1）
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union)


def main():
    """测试工具函数"""
    print("测试专利号清理:")
    print(f"  US-12624481-B1 -> {clean_patent_number('US-12624481-B1')}")
    print(f"  US 12624481 B1 -> {clean_patent_number('US 12624481 B1')}")
    
    print("\n测试文档 ID 提取:")
    print(f"  US12624481B1 -> {extract_doc_id('US12624481B1')}")
    
    print("\n测试专利号验证:")
    print(f"  US-12624481-B1: {is_valid_patent_number('US-12624481-B1')}")
    print(f"  INVALID: {is_valid_patent_number('INVALID')}")
    
    print("\n测试文件名清理:")
    print(f"  file<name>.txt -> {sanitize_filename('file<name>.txt')}")
    
    print("\n测试文本截断:")
    long_text = "This is a very long text that needs to be truncated"
    print(f"  {truncate_text(long_text, 20)}")


if __name__ == "__main__":
    main()

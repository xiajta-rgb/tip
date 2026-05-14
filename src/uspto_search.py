#!/usr/bin/env python3
"""
USPTO 专利检索模块
支持通过 USPTO Patent Public Search Basic 检索专利
"""

import json
import time
import re
from typing import List, Dict, Optional
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import (
    USPTO_SEARCH_URL,
    RESULTS_PER_PAGE,
    REQUEST_TIMEOUT,
    USE_PROXY,
    PROXY_URL,
    MAX_RETRIES,
)


class USPTOSearcher:
    """USPTO 专利检索器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
        # 配置重试策略 - 增加重试次数和延迟
        retry_strategy = Retry(
            total=5,
            backoff_factor=3,
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
    
    def search_by_keyword(self, keyword: str, limit: int = 50) -> List[Dict]:
        """
        通过关键词检索专利
        
        Args:
            keyword: 检索关键词
            limit: 最大结果数量
            
        Returns:
            专利列表，每项包含 patent_number, title, inventor, publication_date, link
        """
        print(f"🔍 正在检索关键词: '{keyword}'...")
        
        patents = self._search_via_google_patents(keyword, limit)
        
        if not patents:
            print(f"⚠️ 未找到与 '{keyword}' 相关的专利")
        else:
            print(f"✅ 找到 {len(patents)} 条相关专利")
            print(f"📥 正在获取专利详细信息...")
            patents = self._enrich_patent_details(patents)
            
        return patents
    
    def _enrich_patent_details(self, patents: List[Dict]) -> List[Dict]:
        """
        获取每个专利的详细信息（法律状态、摘要、分类号、权利要求等）
        
        Args:
            patents: 基本专利列表
            
        Returns:
             enriched 专利列表
        """
        enriched = []
        for i, patent in enumerate(patents, 1):
            pub_num = patent['patent_number']
            print(f"  [{i}/{len(patents)}] 获取 {pub_num} 详情...")
            
            details = self._fetch_patent_details(pub_num)
            if details:
                patent.update(details)
            
            enriched.append(patent)
            time.sleep(0.5)
        
        return enriched
    
    def _fetch_patent_details(self, patent_number: str) -> Optional[Dict]:
        """
        从 Google Patents XHR API 获取详细信息
        
        Args:
            patent_number: 专利号
            
        Returns:
            详细信息字典，失败返回 None
        """
        try:
            url = f"https://patents.google.com/xhr/result"
            params = {
                'id': f'patent/{patent_number}/en',
                'exp': '',
            }
            
            response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            html_content = response.text
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            legal_status = self._extract_status_from_events(soup)
            
            abstract_el = soup.find(attrs={"itemprop": "abstract"})
            abstract = abstract_el.get_text(strip=True) if abstract_el else ''
            if abstract.startswith('Abstract'):
                abstract = abstract[8:].strip()
            
            cpc_codes = []
            ipc_codes = []
            for el in soup.find_all(attrs={"itemprop": "classifications"}):
                text = el.get_text(strip=True)
                is_cpc = el.find_next_sibling(string=lambda s: s and 'IsCPC' in str(s))
                cpc_marker = el.parent.find_next_sibling(string=lambda s: s and 'IsCPC' in str(s)) if el.parent else None
                
                if not cpc_marker:
                    next_sib = el.find_next_sibling()
                    if next_sib and 'IsCPC' in str(next_sib):
                        cpc_codes.append(text)
                    else:
                        ipc_codes.append(text)
                else:
                    cpc_codes.append(text)
            
            expiration_date = self._extract_expiration_from_events(soup, patent_number)
            
            return {
                'legal_status': legal_status,
                'abstract': abstract,
                'cpc_classification': ', '.join(cpc_codes),
                'ipc_classification': ', '.join(ipc_codes),
                'expiration_date': expiration_date,
            }
            
        except Exception as e:
            print(f"  [警告] API获取失败，尝试HTML解析: {str(e)[:50]}")
            return self._extract_from_html(patent_number)
    
    def _extract_status_from_events(self, soup) -> str:
        """从法律事件中提取当前状态"""
        events = soup.find_all(attrs={"itemprop": "legalEvents"})
        if not events:
            return ''
        
        for event in reversed(events):
            title_el = event.find(attrs={"itemprop": "title"})
            if title_el:
                title = title_el.get_text(strip=True).lower()
                if 'expired' in title or 'lapse' in title or 'discontinuation' in title:
                    return 'Expired'
                elif 'grant' in title or 'patent' in title:
                    return 'Active'
        
        status_el = soup.find(attrs={"itemprop": "status"})
        if status_el:
            return status_el.get_text(strip=True)
        
        return ''
    
    def _extract_expiration_from_events(self, soup, patent_number: str) -> str:
        """从法律事件中提取到期日"""
        events = soup.find_all(attrs={"itemprop": "legalEvents"})
        for event in reversed(events):
            title_el = event.find(attrs={"itemprop": "title"})
            if title_el and ('expired' in title_el.get_text(strip=True).lower() or 'lapse' in title_el.get_text(strip=True).lower()):
                date_el = event.find(attrs={"itemprop": "date"})
                if date_el:
                    return date_el.get_text(strip=True)
        
        filing_el = soup.find(attrs={"itemprop": "filing_date"})
        if filing_el:
            filing_date = filing_el.get_text(strip=True)
            pub_type = self._determine_patent_type(patent_number)
            if pub_type in ['实用专利(B1)', '实用专利(B2)']:
                try:
                    year = int(filing_date.split('-')[0])
                    return f"{year + 20}-{filing_date.split('-')[1]}-{filing_date.split('-')[2]}"
                except (ValueError, IndexError):
                    pass
        
        return ''
    
    def _extract_from_html(self, patent_number: str) -> Optional[Dict]:
        """从 HTML 页面提取详细信息（备用方案）"""
        try:
            url = f"https://patents.google.com/patent/{patent_number}/en"
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            html = response.text
            
            legal_status = self._extract_legal_status(html)
            abstract = self._extract_abstract(html)
            cpc_codes, ipc_codes = self._extract_classifications(html)
            claims = self._extract_claims(html)
            expiration_date = self._extract_expiration_date(html, patent_number)
            
            return {
                'legal_status': legal_status,
                'abstract': abstract,
                'cpc_classification': cpc_codes,
                'ipc_classification': ipc_codes,
                'independent_claims': claims,
                'expiration_date': expiration_date,
            }
            
        except Exception as e:
            print(f"  [警告] HTML解析也失败: {str(e)[:50]}")
            return None
    
    def _extract_legal_status(self, html: str) -> str:
        """提取法律状态"""
        match = re.search(r'"legal_status"\s*:\s*"([^"]+)"', html)
        if match:
            return match.group(1)
        
        match = re.search(r'Legal status:\s*<[^>]*>([^<]+)', html)
        if match:
            return match.group(1).strip()
        
        return ''
    
    def _extract_abstract(self, html: str) -> str:
        """提取摘要"""
        match = re.search(r'"abstract"\s*:\s*"((?:[^"\\]|\\.)*)"', html)
        if match:
            return self._clean_html(match.group(1))
        
        match = re.search(r'<div[^>]*class="abstract"[^>]*>(.*?)</div>', html, re.DOTALL)
        if match:
            return self._clean_html(match.group(1))
        
        return ''
    
    def _extract_classifications(self, html: str) -> tuple:
        """提取 CPC 和 IPC 分类号"""
        cpc_codes = []
        ipc_codes = []
        
        cpc_matches = re.findall(r'"cpc"\s*:\s*\[([^\]]*)\]', html)
        for cpc_block in cpc_matches:
            codes = re.findall(r'"code"\s*:\s*"([^"]+)"', cpc_block)
            cpc_codes.extend(codes)
        
        ipc_matches = re.findall(r'"ipc"\s*:\s*\[([^\]]*)\]', html)
        for ipc_block in ipc_matches:
            codes = re.findall(r'"code"\s*:\s*"([^"]+)"', ipc_block)
            ipc_codes.extend(codes)
        
        if not cpc_codes:
            cpc_matches = re.findall(r'"cpc":\s*\[\s*\{[^}]*"code"\s*:\s*"([^"]+)"', html)
            cpc_codes = cpc_matches
        
        if not ipc_codes:
            ipc_matches = re.findall(r'"ipc":\s*\[\s*\{[^}]*"code"\s*:\s*"([^"]+)"', html)
            ipc_codes = ipc_matches
        
        return ', '.join(cpc_codes), ', '.join(ipc_codes)
    
    def _extract_claims(self, html: str) -> str:
        """提取独立权利要求"""
        claims = []
        
        claims_section = re.search(r'"claims"\s*:\s*\[([^\]]*)\]', html, re.DOTALL)
        if claims_section:
            claim_texts = re.findall(r'"text"\s*:\s*"((?:[^"\\]|\\.)*)"', claims_section.group(1))
            for claim_text in claim_texts:
                cleaned = self._clean_html(claim_text)
                if cleaned and not any(ref in cleaned.lower() for ref in ['claim ', 'claims ', 'according to', 'preceding claim']):
                    claims.append(cleaned)
        
        if not claims:
            claims_matches = re.findall(r'<div[^>]*class="claim-text"[^>]*>(.*?)</div>', html, re.DOTALL)
            for i, claim_text in enumerate(claims_matches):
                cleaned = self._clean_html(claim_text)
                if cleaned and (i == 0 or not any(ref in cleaned.lower() for ref in ['claim ', 'according to', 'preceding'])):
                    claims.append(cleaned)
        
        return '\n'.join(claims[:3]) if claims else ''
    
    def _extract_expiration_date(self, html: str, patent_number: str) -> str:
        """提取专利到期日"""
        match = re.search(r'"expiration_date"\s*:\s*"([^"]+)"', html)
        if match:
            return match.group(1)
        
        pub_type = self._determine_patent_type(patent_number)
        filing_match = re.search(r'"filing_date"\s*:\s*"([^"]+)"', html)
        if filing_match and pub_type in ['实用专利(B1)', '实用专利(B2)']:
            filing_date = filing_match.group(1)
            try:
                year = int(filing_date.split('-')[0])
                return f"{year + 20}-{filing_date.split('-')[1]}-{filing_date.split('-')[2]}"
            except (ValueError, IndexError):
                pass
        
        return ''
    
    def _search_via_google_patents(self, query: str, num_results: int = 50) -> List[Dict]:
        """通过 Google Patents API 检索外观专利"""
        # Google Patents API 不支持外观专利过滤，先检索所有专利再过滤
        url = "https://patents.google.com/xhr/query"
        # 增加检索数量以获取更多外观专利
        search_num = min(num_results * 3, 100)
        params = {
            'url': f'q={quote(query)}&num={search_num}',
            'exp': '',
            'content': '1'
        }
        
        # 添加延迟避免被限流
        time.sleep(3)
        
        # 手动重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait_time = 10 * (attempt + 1)
                    print(f"  [重试] 第 {attempt + 1} 次重试，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                
                response = self.session.get(
                    url, 
                    params=params, 
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                
                data = response.json()
                patents = []
                
                for cluster in data.get('results', {}).get('cluster', []):
                    for result in cluster.get('result', []):
                        patent = result.get('patent', {})
                        if not patent:
                            continue
                            
                        pub_num = patent.get('publication_number', '')
                        if not pub_num:
                            continue
                        
                        pub_type = self._determine_patent_type(pub_num)
                        
                        # 保留所有专利类型，后续由 main.py 筛选
                        
                        uspto_link = f"https://ppubs.uspto.gov/pubwebapp/?patentNumber={pub_num}"
                        
                        cpc_codes = patent.get('cpc', [])
                        ipc_codes = patent.get('ipc', [])
                        cpc_str = ', '.join([c.get('code', '') for c in cpc_codes if c.get('code')])
                        ipc_str = ', '.join([c.get('code', '') for c in ipc_codes if c.get('code')])
                        
                        legal_status = patent.get('legal_status', '')
                        
                        abstract = self._clean_html(patent.get('abstract', ''))
                        
                        claims = patent.get('claims', [])
                        independent_claims = []
                        for claim in claims:
                            claim_text = self._clean_html(claim.get('text', ''))
                            if claim_text and not any(ref in claim_text.lower() for ref in ['claim ', 'claims ', 'according to', 'preceding claim']):
                                independent_claims.append(claim_text)
                        claims_str = '\n'.join(independent_claims[:3]) if independent_claims else ''
                        
                        expiration_date = patent.get('expiration_date', '')
                        if not expiration_date:
                            filing_date = patent.get('filing_date', '')
                            if filing_date and pub_type in ['实用专利(B1)', '实用专利(B2)']:
                                try:
                                    year = int(filing_date.split('-')[0])
                                    expiration_date = f"{year + 20}-{filing_date.split('-')[1]}-{filing_date.split('-')[2]}"
                                except (ValueError, IndexError):
                                    pass
                        
                        patents.append({
                            'patent_number': pub_num,
                            'title': self._clean_html(patent.get('title', '')),
                            'inventor': patent.get('inventor', 'Not listed'),
                            'assignee': patent.get('assignee', 'Not listed'),
                            'publication_date': patent.get('publication_date', ''),
                            'filing_date': patent.get('filing_date', ''),
                            'type': pub_type,
                            'link': uspto_link,
                            'snippet': self._clean_html(patent.get('snippet', '')),
                            'abstract': abstract,
                            'cpc_classification': cpc_str,
                            'ipc_classification': ipc_str,
                            'legal_status': legal_status,
                            'expiration_date': expiration_date,
                        })
                        
                        if len(patents) >= num_results:
                            break
                    if len(patents) >= num_results:
                        break
                        
                return patents
                
            except Exception as e:
                print(f"  [警告] Google Patents 检索失败 (尝试 {attempt + 1}/{max_retries}): {str(e)[:80]}")
                if attempt == max_retries - 1:
                    return []
    
    def _determine_patent_type(self, patent_number: str) -> str:
        """根据专利号判断类型"""
        if 'D' in patent_number:
            return "外观设计专利"
        elif patent_number.endswith('B1'):
            return "实用专利(B1)"
        elif patent_number.endswith('B2'):
            return "实用专利(B2)"
        elif patent_number.endswith('A1'):
            return "申请公开(A1)"
        elif patent_number.endswith('A2'):
            return "申请公开(A2)"
        elif 'S' in patent_number:
            return "外观设计专利"
        else:
            return "未知类型"
    
    def _clean_html(self, text: str) -> str:
        """清理 HTML 标签"""
        if not text:
            return ""
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)
        # 解码 HTML 实体
        text = text.replace('&quot;', '"').replace('&amp;', '&')
        text = text.replace('&lt;', '<').replace('&gt;', '>')
        return text.strip()
    
    def search_multiple_keywords(self, keywords: List[str], limit_per_keyword: int = 20) -> List[Dict]:
        """
        批量检索多个关键词
        
        Args:
            keywords: 关键词列表
            limit_per_keyword: 每个关键词的最大结果数
            
        Returns:
            合并后的专利列表（去重）
        """
        all_patents = []
        seen_numbers = set()
        
        for keyword in keywords:
            patents = self.search_by_keyword(keyword, limit_per_keyword)
            
            for p in patents:
                if p['patent_number'] not in seen_numbers:
                    seen_numbers.add(p['patent_number'])
                    all_patents.append(p)
            
            time.sleep(1)  # 避免请求过快
        
        # 按日期排序
        all_patents.sort(
            key=lambda x: x.get('publication_date', '0000-00-00'), 
            reverse=True
        )
        
        return all_patents


def main():
    """测试检索功能"""
    searcher = USPTOSearcher()
    
    # 测试单个关键词
    results = searcher.search_by_keyword("garment", limit=10)
    
    print("\n" + "="*60)
    print("检索结果预览:")
    print("="*60)
    
    for i, p in enumerate(results[:5], 1):
        print(f"\n[{i}] {p['patent_number']}")
        print(f"    标题: {p['title'][:60]}...")
        print(f"    发明人: {p['inventor']}")
        print(f"    日期: {p['publication_date']}")
        print(f"    类型: {p['type']}")


if __name__ == "__main__":
    main()

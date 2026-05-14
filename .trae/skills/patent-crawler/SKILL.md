---
name: "patent-crawler"
description: "执行专利爬取工作流：USPTO品牌搜索->筛选->详情获取->同步到前端。Invoke when user asks to crawl patents or search for brand patents."
---

# Patent Crawler - 专利爬取工作流

## 工作流程

```
品牌关键词搜索(USPTO pubwebapp) -> CSV导出 -> 标题关键词筛选 -> USPTO basic获取详情+PDF+截图 -> 追加到 patent_report_latest.json
```

## 工作流步骤

### Step 1: 品牌关键词搜索并导出 CSV

1. 访问 `https://ppubs.uspto.gov/pubwebapp/`
2. 使用 Playwright 输入品牌关键词
3. 点击 "Export CSV" 下载 CSV 文件
4. 解析 CSV 获取专利 ID 列表

**源文件**: [brand_search_async.py](file:///c:\Users\xiajt\Desktop\patent_crawler\src\brand_search_async.py)

### Step 2: 标题关键词筛选

1. 读取导出的 CSV
2. 根据 `config.py` 中的 `CATEGORY_KEYWORDS` 筛选标题
3. 匹配关键词的专利进入下一步

**源文件**: [patent_filter.py](file:///c:\Users\xiajt\Desktop\patent_crawler\src\patent_filter.py)

### Step 3: 获取专利详情

1. 访问 `https://ppubs.uspto.gov/basic/#`
2. 逐个获取筛选后专利的：
   - 详细信息（标题、摘要、申请人、发明人等）
   - PDF 下载
   - 截图生成

**源文件**: [uspto_search.py](file:///c:\Users\xiajt\Desktop\patent_crawler\src\uspto_search.py)

### Step 4: 同步到前端

1. 生成独立报告文件（如 `output/patent_report_YYYYMMDD_HHMMSS.json`）
2. **增量追加**到 `output/patent_report_latest.json`
3. 下载 PDF 到 `output/pdfs/`
4. 生成截图到 `output/screenshots/`

## 配置

品牌关键词在 [config.py](file:///c:\Users\xiajt\Desktop\patent_crawler\config.py) 中配置：

```python
CATEGORY_KEYWORDS = [
    "T-shirt", "Polo shirt", "Blouse", "Sweater", "Hoodie", "Jacket", "Coat", "Vest",
    "Jeans", "Pants", "Shorts", "Skirt", "Dress", "Coverall", "Jumpsuit", "Suit", "Romper", "Bodysuit",
    "Lounge set", "Two-piece", "Co-ord", "Matching set", "Outerwear", "Sweatshirt", "Linen shirt", "Flannel shirt"
]
```

## 执行方式

```bash
# 主入口
python main.py --brands "NIKE,Adidas" --limit 50

# 或分步执行
python src/brand_search_async.py --brand "NIKE"
python src/filter_and_download.py --csv output/downloads/xxx.csv
```

## 输出文件

| 文件 | 说明 |
|------|------|
| `output/patent_report_latest.json` | 主数据文件（前端使用） |
| `output/patent_report_YYYYMMDD_HHMMSS.json` | 独立运行记录 |
| `output/pdfs/*.pdf` | 专利 PDF 文件 |
| `output/screenshots/*.png` | 专利截图 |

## JSON 格式

```json
{
  "generated_at": "2026-05-15 01:22:54",
  "total_count": 12,
  "patents": [
    {
      "patent_number": "US D1084605 S",
      "patent_number_clean": "D1084605",
      "title": "Jacket",
      "type": "design patent",
      "abstract": "Jacket",
      "publication_date": "2025-07-22",
      "assignee": "Aritzia LP",
      "inventor": "Okada; Jean Liye et al.",
      "matched_keywords": ["jacket"],
      "pdf_path": "C:\\Users\\...\\output\\pdfs\\D1084605.pdf",
      "screenshot_path": "C:\\Users\\...\\output\\screenshots\\D1084605_page1.png",
      "link": "https://patents.google.com/patent/D1084605/en"
    }
  ]
}
```

## 注意事项

1. **增量同步**: 新专利追加到 `patent_report_latest.json`，避免覆盖已有数据
2. **去重**: 根据 `patent_number` 去重，相同的专利不重复添加
3. **PDF/截图命名**: 使用 `patent_number_clean`（如 `D1084605`）命名文件
4. **前端兼容性**: 前端 [app.js](file:///c:\Users\xiajt\Desktop\patent_crawler\frontend\js\app.js#L385) 已使用 `patent_number_clean` 匹配文件
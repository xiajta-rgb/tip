---
name: "patent-crawler"
description: "执行专利爬取工作流：USPTO品牌搜索->CSV打标审查->PDF采集->同步到前端。Invoke when user asks to crawl patents or search for brand patents."
---

# Patent Crawler - 专利爬取工作流

## 工作流程

```
品牌关键词搜索(USPTO pubwebapp) -> CSV导出 -> 批量自动打标(服装类型) -> 用户审查维护 -> 仅采集标记为是的专利 -> 追加到 patent_report_latest.json
```

## 工作流步骤

### Step 1: 品牌关键词搜索并导出 CSV

1. 访问 `https://ppubs.uspto.gov/pubwebapp/`
2. 使用 Playwright 输入品牌关键词（如 "NIKE"）
3. 点击 "Export CSV" 下载 CSV 文件
4. 保存到 `downloads/{品牌名}.csv`

### Step 2: CSV 批量自动打标

1. 读取导出的 CSV
2. **在第一列添加"标签"字段**，根据标题关键词自动分类：
3. **在第二列添加"采集"字段**，默认值为 `N`

### Step 3: 用户审查维护（关键步骤）

1. **提示用户**打开 CSV 文件进行人工审查
2. 用户可以：
   - 修改标签列，调整分类
   - 修改采集列，决定是否采集：
     - `Y` - 采集 PDF
     - `N` - 跳过
3. **等待用户输入 Y 确认继续**
4. 读取用户确认后的 CSV，仅处理采集列=`Y` 的专利

### Step 4: 采集标记的专利 PDF

1. 启动 Playwright 浏览器
2. 对采集列=`Y` 的专利：
   - 搜索专利号
   - 下载每页图片
   - 合并为 PDF
   - 提取首页截图
3. 保存到 `output/pdfs/` 和 `output/screenshots/`

### Step 5: 增量追加到前端数据

1. 读取现有的 `patent_report_latest.json`
2. 根据 `patent_number` 去重
3. 合并新旧专利数据
4. 保存为最新报告

## 关键词库（重要经验）

### 关键词分类规则

```python
LABEL_KEYWORDS = {
    '上装': ['t-shirt', 'tshirt', 'blouse', 'sweater', 'hoodie', 'jersey', 'tunic', 'pullover', 'henley', 'camisole', 'bodice', 'crop top', 'shirt', 'cardigan', 'vest', 'bralette', 'sweatshirt', 'sleeveless', 'tank top'],

    '下装': ['jeans', 'pants', 'shorts', 'trouser', 'chinos', 'bermuda', 'cargo', 'jogger', 'culotte', 'capri', 'palazzo'],

    '套装': ['lounge set', 'two-piece', 'co-ord', 'suit', 'ensemble', 'coordinate', 'jumpsuit', 'romper', 'matching set', 'track suit'],

    '外套': ['jacket', 'coat', 'vest', 'parka', 'blazer', 'windbreaker', 'cape', 'cloak', 'anorak', 'raincoat', 'overcoat', 'outerwear', 'parkas', 'fleece', 'softshell', 'bomber', 'puffer', 'gilet', 'wind vest'],

    '连衣裙': ['dress', 'gown', 'frock', 'one-piece', 'maxi', 'midi', 'cocktail dress', 'sheath dress', 'wrap dress'],

    '头饰': ['hijab', 'scarf', 'bandana', 'shawl', 'turban', 'headband', 'hat', 'cap', 'beanie', 'visor', 'headwear'],

    '面罩': ['mask', 'goggle', 'face shield', 'eye protection', 'safety glasses'],

    '腕带': ['watch band', 'smart band', 'wearable band', 'strap', 'bracelet'],

    '包袋': ['bag', 'backpack', 'handbag', 'tote', 'purse', 'pouch', 'wallet', 'clutch', 'luggage'],

    '服装面料': ['textile', 'fabric', 'woven', 'knit', 'nonwoven', 'laminate', 'foam', 'cushion', 'bladders'],

    '可穿戴': ['wearable', 'wearable article', 'apparel', 'garment', 'support garment', 'clothing'],

    '智能设备': ['smart watch', 'smart band', 'fitness tracker', 'wearable device', 'smart device'],

    '鞋类': ['shoe', 'footwear', 'boot', 'sandal', 'slipper', 'sneaker', 'outsole', 'midsole', 'insole', 'loafer', 'moccasin', 'cleat', 'spike'],
}
```

### 关键词匹配规则

```python
def auto_label(title: str) -> tuple:
    """根据标题自动打标"""
    title_lower = title.lower()

    # 遍历关键词库
    for label, keywords in LABEL_KEYWORDS.items():
        for kw in keywords:
            if kw in title_lower:
                # 鞋类返回 N（跳过）
                if label == '鞋类':
                    return ('鞋类', 'N')
                else:
                    return (label, 'Y')

    # 未匹配任何关键词，默认跳过
    return ('其他', 'N')
```

### 实用专利检测规则

```python
# 检测是否为外观设计专利（US D 格式）
def is_design_patent(doc_id: str) -> bool:
    return doc_id.startswith('US D') or doc_id.startswith('D')

# 实用专利（US 数字格式）默认跳过
if not is_design_patent(doc_id):
    return ('实用专利', 'N')
```

## CSV 格式

打标后的 CSV：
| 标签 | 采集 | Document ID | Title | ... |
|------|------|-------------|-------|------|
| 外套 | Y | US D1121234 S | Jacket | ... |
| 鞋类 | N | US 12345678 B2 | Shoe | ... |

## 执行方式

```bash
# 品牌爬取
python run_brand_workflow.py --brand "NIKE" --limit 100 --no-headless

# 只打标
python src/csv_labeler.py downloads/NIKE.csv
```

## 输出文件

| 文件 | 说明 |
|------|------|
| `downloads/{品牌}_labeled.csv` | 打标后的 CSV |
| `output/patent_report_latest.json` | 前端数据（增量追加） |
| `output/pdfs/*.pdf` | PDF 文件 |
| `output/screenshots/*.png` | 截图 |

## 注意事项

1. **关键词匹配不区分大小写**（转小写后匹配）
2. **鞋类自动跳过**（采集=N）
3. **实用专利自动跳过**（非 US D/D 格式）
4. **未匹配任何关键词的默认跳过**（采集=N）
5. **增量追加**：新专利追加到 `patent_report_latest.json`，去重后保存
6. **截图优化**：优先截取专利图片，精确裁剪去除空白
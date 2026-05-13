# USPTO 专利爬虫工具包

一套完整的 USPTO（美国专利商标局）专利检索、下载和报告生成工具。

## 📋 功能特性

- 🔍 **智能检索**: 通过 USPTO Patent Public Search 检索专利
- 📥 **PDF 下载**: 自动下载专利 PDF 文件
- 🖼️ **截图提取**: 提取专利首页截图（含三视图）
- 📊 **报告生成**: 生成 Excel 和 JSON 格式的完整报告
- 🏷️ **风险分类**: 自动分析侵权风险关键词

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行主程序

```bash
# 完整流程：检索 + 下载 + 报告
python main.py --keyword "garment" --limit 20

# 仅检索（不下载PDF）
python main.py --keyword "smart garment" --limit 10 --no-download

# 从已有报告下载PDF
python main.py --from-report patent_report.json --download-only
```

### 3. 查看结果

- `output/patent_report.xlsx` - Excel 报告
- `output/pdfs/` - PDF 文件
- `output/screenshots/` - 首页截图

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `main.py` | 主入口程序 |
| `src/uspto_search.py` | USPTO 网站检索模块 |
| `src/patent_downloader.py` | PDF 下载和截图模块 |
| `src/report_generator.py` | 报告生成模块 |
| `config.py` | 配置文件 |

## 🔧 配置选项

编辑 `config.py` 可自定义：

- 检索关键词
- 每页结果数量
- 下载延迟（防封）
- 输出目录
- 代理设置

## 📝 使用示例

### 示例 1: 检索服装相关专利

```bash
python main.py --keyword "garment" --limit 50
```

### 示例 2: 检索智能穿戴专利并下载

```bash
python main.py --keyword "smart wearable sensor" --limit 20 --download
```

### 示例 3: 仅生成报告（使用已有数据）

```bash
python main.py --from-json patent_results.json
```

## 🌐 数据来源

- **检索**: https://ppubs.uspto.gov/basic/
- **PDF**: https://pdfpiw.uspto.gov/
- **备用**: https://patents.google.com/

## ⚠️ 注意事项

1. **网络限制**: 某些网络环境可能需要配置代理
2. **频率限制**: USPTO 有访问频率限制，建议设置合理延迟
3. **PDF 下载**: 大量下载时建议使用 `--delay` 参数避免被封

## 📄 报告字段

生成的报告包含以下字段：

- 序号
- 专利号
- 专利标题
- 发明人
- 公布日期
- 专利类型（实用/外观/申请）
- USPTO 链接
- PDF 下载链接
- Google Patents 链接
- 侵权风险关键词分类

## 🔒 免责声明

本工具仅供学习和研究使用，请遵守 USPTO 的使用条款和相关法律法规。

## 📧 支持

如有问题，请检查：
1. 网络连接是否正常
2. 依赖是否完整安装
3. 配置文件是否正确

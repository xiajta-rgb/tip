#!/usr/bin/env python3
"""
USPTO 专利爬虫配置文件
"""

import os

# ========== 检索配置 ==========

# 默认检索关键词
DEFAULT_KEYWORDS = [
    "garment",           # 服装
    "outwear",          # 户外服装
    "vest",            # 背心
    "smart garment",     # 智能服装
    "wearable sensor",   # 可穿戴传感器
    "heated clothing",   # 加热服装
    "compression garment", # 压缩服装
]

# 服装行业关键词（用于后端过滤）
GARMENT_KEYWORDS = [
    "garment", "clothing", "apparel", "wear", "textile", "fabric", "fashion", "outerwear","vset","hoodie","jacket","pants","suit",
    "footwear", "shoe", "sneaker", "boot", "sandals",
    "hat", "cap", "belt", "glove", "scarf", "sock",
    "underwear", "bra", "panty", "lingerie",
    "shirt", "blouse", "t-shirt", "tshirt", "pants", "trouser", "skirt",
    "dress", "jacket", "coat", "hoodie", "sweater", "shorts", "jean",
    "suit", "tie", "uniform", "yoga", "athletic", "sportswear"
]

# 每页结果数量
RESULTS_PER_PAGE = 50

# 最大检索页数
MAX_PAGES = 1

# ========== 下载配置 ==========

# 下载延迟（秒）- 防止被封
DOWNLOAD_DELAY = 2

# 最大重试次数
MAX_RETRIES = 3

# 超时设置（秒）
REQUEST_TIMEOUT = 30

# 是否使用代理
USE_PROXY = False
PROXY_URL = "http://127.0.0.1:8080"  # 如需代理，请修改

# ========== 输出配置 ==========

# 基础输出目录
BASE_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

# PDF 输出目录
PDF_OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, "pdfs")

# 截图输出目录
SCREENSHOT_OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, "screenshots")

# 报告输出目录
REPORT_OUTPUT_DIR = BASE_OUTPUT_DIR

# ========== USPTO 链接模板 ==========

# USPTO 检索页面
USPTO_SEARCH_URL = "https://ppubs.uspto.gov/basic/"

# USPTO PDF 下载链接模板（直接PDF链接）
USPTO_PDF_URL_TEMPLATE = "https://ppubs.uspto.gov/pubwebapp/pdf/{doc_id}.pdf"

# USPTO 公开检索链接模板
USPTO_PUBWEB_URL_TEMPLATE = "https://ppubs.uspto.gov/pubwebapp/?patentNumber=US-{patent_number}"

# ========== USPTO 官方 API 配置 ==========

# USPTO Open Data Portal API 基础 URL
USPTO_API_BASE_URL = "https://api.uspto.gov/api/v1"

# USPTO API Key（需要到 https://data.uspto.gov/apis/getting-started 申请）
# 留空则不使用官方 API
USPTO_API_KEY = ""

# USPTO 专利检索 API 端点
USPTO_PATENT_SEARCH_URL = f"{USPTO_API_BASE_URL}/patent/applications/search"

# ========== 侵权风险关键词分类 ==========

RISK_KEYWORDS = {
    "智能穿戴": ["smart", "wearable", "sensor", "monitor", "track", "fitness", "health"],
    "医疗健康": ["medical", "health", "therapy", "treatment", "diagnostic", "surgical", "patient"],
    "纺织品/面料": ["fabric", "textile", "fiber", "woven", "knit", "yarn", "material"],
    "吸收性用品": ["absorbent", "diaper", "sanitary", "pad", "wipe", "tissue"],
    "增强现实/虚拟现实": ["augmented reality", "virtual reality", "AR", "VR", "mixed reality"],
    "机器人/自动化": ["robot", "automation", "automated", "mechanical", "actuator"],
    "数据安全": ["security", "encryption", "authentication", "privacy", "secure"],
    "热管理/防护": ["thermal", "heat", "cooling", "insulation", "flame-resistant", "protective"],
    "成像/光学": ["imaging", "optical", "camera", "lens", "display", "visualization"],
    "音频技术": ["audio", "sound", "acoustic", "speaker", "microphone", "hearing"],
}

# ========== 日志配置 ==========

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# ========== 浏览器配置（用于高级检索） ==========

# 浏览器类型: "chrome", "firefox", "edge"
BROWSER_TYPE = "chrome"

# 无头模式
HEADLESS = True

# 浏览器窗口大小
BROWSER_WINDOW_SIZE = (1920, 1080)

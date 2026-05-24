#!/usr/bin/env python3
"""USPTO 爬虫配置文件"""
import os

# 输出目录
BASE_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
SCREENSHOT_OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, "screenshots")
PDF_OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, "pdfs")

# USPTO 配置
USPTO_SEARCH_URL = "https://ppubs.uspto.gov/basic/#/search/basic"
USPTO_PDF_URL = "https://pdfpiw.uspto.gov/.pptd/"
USPTO_PDF_URL_TEMPLATE = "https://pdfpiw.uspto.gov/.pptd/{doc_id}/1"
RESULTS_PER_PAGE = 100
USE_PROXY = False
PROXY_URL = ""

# 报告配置
REPORT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
RISK_KEYWORDS = {
    "侵权风险": ["infringement", "patent", "claim", "scope", "enforce"],
    "诉讼风险": ["lawsuit", "violation", "exclusive"],
    "法律风险": ["legal", "rights", "protection"]
}

# 检索配置
CATEGORY_KEYWORDS = [
    "T-shirt", "Polo shirt", "Blouse", "Sweater", "Hoodie", "Jacket", "Coat", "Vest",
    "Jeans", "Pants", "Shorts", "Skirt", "Dress", "Coverall", "Jumpsuit", "Suit", "Romper", "Bodysuit",
    "Lounge set", "Two-piece", "Co-ord", "Matching set", "Outerwear", "Sweatshirt", "Linen shirt", "Flannel shirt"
]

GARMENT_KEYWORDS = [
    "T-shirt", "Polo shirt", "Blouse", "Sweater", "Hoodie", "Jacket", "Coat", "Vest",
    "Jeans", "Pants", "Shorts", "Skirt", "Dress", "Coverall", "Jumpsuit", "Suit", "Romper", "Bodysuit",
    "Lounge set", "Two-piece", "Co-ord", "Matching set", "Outerwear", "Sweatshirt", "Linen shirt", "Flannel shirt",
    "Shirt", "Top", "Bottom", "Apparel", "Garment", "Clothing", "Hijab", "Skort", "Legging", "Tank", "Capri",
    "Bikini", "Swimsuit", "Swimwear", "Bra", "Underwear", "Lingerie", "Panty", "Brief", "Boxer"
]

SHOE_KEYWORDS = [
    'shoe', 'footwear', 'boot', 'sandal', 'slipper', 'sneaker',
    'outsole', 'midsole', 'insole', 'athletic shoe', 'running shoe',
    'basketball shoe', 'tennis shoe', 'casual shoe', 'dress shoe'
]

DEFAULT_KEYWORDS = ["garment", "clothing", "apparel"]

BRAND_KEYWORDS = ["Nike", "Adidas", "Puma", "Under Armour", "Zara", "H&M", "Uniqlo"]

CATEGORY_ALIASES = {
    "T-shirt": ["tee", "t shirt", "tshirt"],
    "Jacket": ["jackets", "jacket"],
    "Pants": ["pant"],
}

# 浏览器配置
HEADLESS = False
BROWSER_TYPE = "chrome"
BROWSER_WINDOW_SIZE = (1920, 1080)
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

# 下载配置
DOWNLOAD_DELAY = 1
MAX_PARALLEL_DOWNLOADS = 3

# Google Patents API
GOOGLE_PATENTS_API = "https://patents.google.com/xhr/result"

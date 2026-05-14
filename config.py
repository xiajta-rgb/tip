#!/usr/bin/env python3
"""USPTO 爬虫配置文件"""
import os

# 输出目录
BASE_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
SCREENSHOT_OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, "screenshots")
PDF_OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, "pdfs")

# 检索配置
CATEGORY_KEYWORDS = [
    "T-shirt", "Polo shirt", "Blouse", "Sweater", "Hoodie", "Jacket", "Coat", "Vest",
    "Jeans", "Pants", "Shorts", "Skirt", "Dress", "Coverall", "Jumpsuit", "Suit", "Romper", "Bodysuit",
    "Lounge set", "Two-piece", "Co-ord", "Matching set", "Outerwear", "Sweatshirt", "Linen shirt", "Flannel shirt"
]

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

import re

from dotenv import dotenv_values

WEBSITE = dotenv_values(".env")["WEBSITE"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    + "(KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
}

CATEGORY_URL_REGEX = re.compile(
    rf"^https://www.{WEBSITE}.com/([a-z]+)/([a-z-/]+)/cat/\?cid=([0-9]+)$"
)

PAGINATION_REGEX = re.compile(r"You've viewed ([0-9,]+) of ([0-9,]+) products$")

# these have been scraped manually as it's just a handful of them
MORE_CATEGORIES = {
    4172: {
        "gender": "women",
        "category": "shoes",
        "subcategory": "shoes",
        "base_url": f"https://www.{WEBSITE}.com/women/shoes/cat/?cid=4172",
    },
    4174: {
        "gender": "women",
        "category": "accessories",
        "subcategory": "accessories",
        "base_url": f"https://www.{WEBSITE}.com/women/accessories/cat/?cid=4174",
    },
    4209: {
        "gender": "men",
        "category": "shoes-boots-trainers",
        "subcategory": "shoes-boots-trainers",
        "base_url": f"https://www.{WEBSITE}.com/men/shoes-boots-trainers/cat/?cid=4209",
    },
    4210: {
        "gender": "men",
        "category": "accessories",
        "subcategory": "accessories",
        "base_url": f"https://www.{WEBSITE}.com/men/accessories/cat/?cid=4210",
    },
}

BATCH_SIZE = 10_000

DATABASE_NAME = f"{WEBSITE}_data.db"

CATEGORIES_TABLE = """
id INTEGER PRIMARY KEY,
gender TEXT,
category TEXT,
subcategory TEXT,
base_url TEXT
"""

PAGES_URLS_TABLE = """
id INTEGER,
page_url TEXT PRIMARY KEY
"""

ARTICLES_URLS_TABLE = """
id INTEGER,
page_url TEXT,
article_url TEXT PRIMARY KEY
"""

ARTICLES_DATA_TABLE = """
id INTEGER,
article_url TEXT PRIMARY KEY,
description TEXT,
colour TEXT,
tags TEXT,
materials TEXT,
images_urls TEXT
"""

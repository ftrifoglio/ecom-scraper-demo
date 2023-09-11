"""webscraper package."""

from .asyncio import (
    compile_article_data,
    compile_article_urls,
    compile_page_urls,
    make_requests,
)
from .database import TableHandler
from .scraping import extract_categories_urls

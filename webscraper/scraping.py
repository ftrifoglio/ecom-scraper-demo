"""Scraping functions."""

import json
import math
import re
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag

from ._constants import (
    CATEGORY_URL_REGEX,
    HEADERS,
    MORE_CATEGORIES,
    PAGINATION_REGEX,
    WEBSITE,
)


def extract_categories_urls() -> list[dict]:
    """
    Extract the URLs for the Clothing sub-categories in a given HTML string.

    The URLs for shoes and accessories in MORE_CATEGORIES are added too.

    Returns
    -------
    list[dict]
        A list of extracted categories URLs.

    """
    r = requests.get(f"https://www.{WEBSITE}.com", headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    try:
        # the page contains the navbar for both men and women
        nav_buttons = [
            b
            for b in soup.find_all("button", {"data-testid": "primarynav-button"})
            if b.text == "Clothing"
        ]
        # nav_buttons contains the Clothing navbar buttons for both men and women
        list_items = [
            b.find_next_sibling("div").find("ul").find_all("li") for b in nav_buttons
        ]
        # list_items contains the secondary navbar for Clothing for both men and women
        hrefs = [li.next.attrs["href"] for ul in list_items for li in ul]
        # hrefs contains all the URLs
        hrefs_clean = [
            re.findall(r"(^.*)#nlid=.*$", href)[0]
            for href in hrefs
            if "cid=" in href and "ctas" not in href and "new-in" not in href
        ]
        # extract relevant information from the URL and itself
        tuples_list = [
            (href,) + match.groups()
            for href in hrefs_clean
            if (match := CATEGORY_URL_REGEX.search(href)) is not None
        ]
        categories = {
            int(t[3]): {
                "gender": t[1],
                "category": "clothing",
                "subcategory": t[2],
                "base_url": t[0],
            }
            for t in tuples_list
        }
        categories = categories | MORE_CATEGORIES
    except AttributeError:
        categories = MORE_CATEGORIES
    return [{"id": k, **v} for k, v in categories.items()]


async def extract_article_urls(html: str) -> list[str] | None:
    """
    Extract URLs from articles in a given HTML string.

    Parameters
    ----------
    html : str
        The HTML string from which the article URLs need to be extracted.

    Returns
    -------
    list[str] | None
        A list of extracted article URLs.

    Examples
    --------
    >>> sample_html = '''<div><article><a href="http://example.com/article1"></a></article>
    ...               <article><a href="http://example.com/article2"></a></article></div>'''
    >>> article_urls = await extract_article_urls(sample_html)
    >>> print(article_urls)
    ['http://example.com/article1', 'http://example.com/article2']
    """
    soup = BeautifulSoup(html, "html.parser")
    try:
        return [article.find("a").attrs["href"] for article in soup.find_all("article")]
    except AttributeError:
        return None


async def extract_total_pages(
    html: str,
) -> int:
    """
    Extract total pages in a a category.

    It does so by extracting the number of articles per page and total number of
    articles from a given HTML string pattern and calculating the total number of
    pages per category.

    Parameters
    ----------
    html : str
        The HTML string containing the pattern "You've viewed {} of {} products".

    Returns
    -------
    int | None
        The total number of pages.

    Examples
    --------
    >>> html = '''<div><p>You've viewed 72 of 12,911 products</p><progress></progress>
    ...        </div>'''
    >>> total_pages = await extract_total_pages(html)
    >>> print(total_pages)
    180
    """
    soup = BeautifulSoup(html, "html.parser")
    bs_match = soup.find("progress")
    total_pages = 1
    if bs_match:
        re_match = PAGINATION_REGEX.search(str(bs_match.previous))
        if re_match:
            articles_per_page, total_articles = re_match.groups()
            articles_per_page = int(articles_per_page.replace(",", ""))
            total_articles = int(total_articles.replace(",", ""))
            total_pages = math.ceil(total_articles / articles_per_page)
    return total_pages


async def extract_article_data(
    html: str,
) -> tuple[
    str | None, str | None, list[str] | None, list[str] | None, list[str] | None
]:
    """
    Extract description, colour, tags, materials and image URLs in a given HTML string.

    Parameters
    ----------
    html : str
        The HTML string from which the article data need to be extracted.

    Returns
    -------
    tuple[str | None, str | None, list[str] | None, list[str] | None, list[str] | None]
        A list of extracted article data.
    """
    description: str | None = None
    colour: str | None = None
    tags: list[str] | None = None
    materials: list[str] | None = None
    img_urls: list[str] | None = None

    # conveniently most of the data can be found in a json string at the top of the
    # html file, so we don't even need bs4 for this
    re_match = re.search(f"window.{WEBSITE}.pdp.config.product = (.*);", html)
    if re_match:
        json_string = re_match.group(1)
        product_config: dict[str, Any] = json.loads(json_string)
        # description
        if "name" in product_config.keys():
            description = product_config["name"]
            if isinstance(description, str):
                description = description.strip().lower()
        # colour and img_urls
        if "images" in product_config.keys():
            images: list[dict[str, str]] = [
                {k: d.get(k, "") for k in ["url", "colour"]}
                for d in product_config["images"]
            ]
            colours = [
                d["colour"]
                for d in images
                if "colour" in d.keys() and len(d["colour"]) > 0
            ]
            if colours:
                colour = colours[0].strip().lower()
            img_urls_list = [d["url"] for d in images if "url" in d.keys()]
            if img_urls_list:
                img_urls = img_urls_list

    # use bs4 to extract materials and tags
    soup = BeautifulSoup(html, "html.parser")
    bs_div_match = soup.find("div", {"id": "productDescriptionDetails"})
    if isinstance(bs_div_match, Tag):
        bs_li_match = bs_div_match.find_all("li")
        if bs_li_match:
            tags = [
                li.text.strip().lower()
                for li in bs_li_match
                if isinstance(li.text, str)
            ]
    bs_div_match = soup.find("div", {"id": "productDescriptionAboutMe"})
    if bs_div_match:
        materials = bs_div_match.get_text(separator="\n").strip().lower().splitlines()

    return description, colour, tags, materials, img_urls

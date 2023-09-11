#!/usr/bin/env python

"""E-commerce site scraping application."""

import asyncio

from loguru import logger

from webscraper import (
    TableHandler,
    compile_article_data,
    compile_article_urls,
    compile_page_urls,
    extract_categories_urls,
    make_requests,
)

CONCURRENCY_LIMIT = 100


async def scrape_ecommerce_site() -> None:
    """Scrape the ecommerce site."""
    logger.info("[1/4] Getting categories URLs...")
    categories = extract_categories_urls()
    categories_table = TableHandler("categories")
    categories_table.insert_into(categories)
    logger.success("[1/4] Completed")

    logger.info("[2/4] Getting pages URLs...")
    pages_urls_table = TableHandler("pages_urls")
    _, failed = await make_requests(
        compile_page_urls,
        categories,
        concurrency_limit=CONCURRENCY_LIMIT,
        table_handler=pages_urls_table,
    )
    if failed:
        logger.error(f"[2/4] {len(failed)} of {len(categories)} requests failed")
    logger.success("[2/4] Completed")

    logger.info("[3/4] Getting articles URLs...")
    pages_urls = pages_urls_table.to_pandas().to_dict("records")
    articles_urls_table = TableHandler("articles_urls")
    _, failed = await make_requests(
        compile_article_urls,
        pages_urls,
        concurrency_limit=CONCURRENCY_LIMIT,
        table_handler=articles_urls_table,
    )
    if failed:
        logger.error(f"[3/4] {len(failed)} of {len(pages_urls)} requests failed")
    logger.success("[3/4] Completed")

    logger.info("[4/4] Getting articles data...")
    articles_urls = articles_urls_table.to_pandas().to_dict("records")
    articles_data_table = TableHandler("articles_data")
    _, failed = await make_requests(
        compile_article_data,
        articles_urls,
        concurrency_limit=CONCURRENCY_LIMIT,
        table_handler=articles_data_table,
    )
    if failed:
        logger.error(f"[4/4] {len(failed)} of {len(articles_urls)} requests failed")
    logger.success("[4/4] Completed")


if __name__ == "__main__":
    asyncio.run(scrape_ecommerce_site())

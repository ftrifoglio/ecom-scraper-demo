"""Asynchronous functions."""

import asyncio
import json
from functools import partial
from typing import Any, Callable, Coroutine, Iterable

import aiohttp

from ._constants import BATCH_SIZE, HEADERS
from .database import TableHandler
from .scraping import extract_article_data, extract_article_urls, extract_total_pages
from .utils import flatten


class TooManyRetries(Exception):
    """
    Exception raised when there are too many retries for a specific URL.

    Attributes
    ----------
    params : any
        The params of the coroutine that had too many retries.
    """

    def __init__(self, params: dict):
        super().__init__(f"Too many retries for params: {params}")
        self._params = params

    @property
    def params(self) -> dict:
        """The params of the coroutine that had too many retries."""
        return self._params


async def retry(
    coro: Callable[[dict], Coroutine[Any, Any, list[dict[str, Any]]]],
    params: dict,
    max_retries: int = 5,
    timeout: float = 10.0,
    backoff_factor: float = 1.0,
) -> list[dict[str, Any]]:
    """
    Wait for a coroutine and retry it if needed.

    Parameters
    ----------
    coro : callable
        The async function that needs to be retried.
    params : dict
        Parameters of the async function.
    max_retries : int, optional
        Maximum number of retries. Default is 5.
    timeout : float, optional
        Timeout in seconds for the coroutine. Default is 10.0 seconds.
    backoff_factor : float, optional
        Factor to calculate the delay between retries. Default is 1.0.

    Returns
    -------
    list[dict]
        The result of the coroutines. One of:
        1. compile_page_urls -> list[dict]
        2. compile_article_urls -> list[dict]
        3. compile_article_data -> list[dict]

    Raises
    ------
    TooManyRetries
        If the coroutine fails for max_retries times.

    Examples
    --------
    >>> async def sample_coro():
    ...     # some asynchronous operation
    ...     pass
    >>> result = await retry(sample_coro(), "http://example.com")
    """
    retry_interval = 0.0
    for i in range(max_retries):
        try:
            return await asyncio.wait_for(coro(params), timeout=timeout)
        except Exception:
            await asyncio.sleep(retry_interval)
            retry_interval = backoff_factor * (2**i)
    raise TooManyRetries(params)


async def compile_page_urls(
    session: aiohttp.ClientSession, category_dict: dict
) -> list[dict[str, Any]]:
    """
    Compile the page URLs for each category.

    Parameters
    ----------
    session : aiohttp.ClientSession
        The current session to make the HTTP request.
    category_dict : dict
        The category's details, including the base URL.

    Returns
    -------
    list[dict[str, Any]]
        A list of a dictionaries, each containing the category id and the
        compiled URLs for each page in the category.

    Examples
    --------
    >>> session = aiohttp.ClientSession()
    >>> category_dict = {"base_url": "http://example.com/category1"}
    >>> page_urls = await compile_page_urls(session, category_dict)
    """

    def _paginate(category_dict: dict) -> list[dict]:
        return [
            {
                "id": category_dict["id"],
                "page_url": category_dict["base_url"] + "&page=" + str(p),
            }
            for p in range(1, total_pages + 1)
        ]

    async with session.get(category_dict["base_url"]) as response:
        html = await response.text()
        total_pages = await extract_total_pages(html)
    return _paginate(category_dict)


async def compile_article_urls(
    session: aiohttp.ClientSession, page_dict: dict
) -> list[dict[str, Any]]:
    """
    Compile the article URLs for each page.

    Parameters
    ----------
    session : aiohttp.ClientSession
        The current session to make the HTTP request.
    page_dict : dict
        The page details so far, including its link.

    Returns
    -------
    list[dict[str, Any]]
        A list of dictionaries, each containing the category id,
        the page URL being scraped and the URLs of each article
        on the page.

    Examples
    --------
    >>> session = aiohttp.ClientSession()
    >>> page_dict = {"page_url": "http://example.com/page1"}
    >>> article_urls = await compile_article_urls(session, page_dict)
    """
    async with session.get(page_dict["page_url"]) as response:
        html = await response.text()
        article_urls = await extract_article_urls(html)
        if article_urls:
            return [
                {
                    "id": page_dict["id"],
                    "page_url": page_dict["page_url"],
                    "article_url": url,
                }
                for url in article_urls
            ]
        else:
            return [
                {
                    "id": page_dict["id"],
                    "page_url": page_dict["page_url"],
                    "article_url": None,
                }
            ]


async def compile_article_data(
    session: aiohttp.ClientSession, article_dict: dict
) -> list[dict[str, Any]]:
    """
    Compile the data for each article.

    The data are:
    - description (str)
    - colour (str)
    - tags (serialized JSON str)
    - materials (serialized JSON str)
    - images URLs (serialized JSON str)

    Parameters
    ----------
    session : aiohttp.ClientSession
        The current session to make the HTTP request.
    article_dict : dict
        The article's details, including its link.

    Returns
    -------
    dict[str, Any]
        Dictionary containing the data of the article.

    Examples
    --------
    >>> session = aiohttp.ClientSession()
    >>> article_dict = {"article_url": "http://example.com/article1"}
    >>> articles_data = await compile_article_data(session, article_dict)
    """
    article_dict = article_dict.copy()
    async with session.get(article_dict["article_url"]) as response:
        html = await response.text()
        (
            description,
            colour,
            tags,
            materials,
            img_urls,
        ) = await extract_article_data(html)
        article_dict["description"] = description
        article_dict["colour"] = colour
        article_dict["tags"] = json.dumps(tags)
        article_dict["materials"] = json.dumps(materials)
        article_dict["img_urls"] = json.dumps(img_urls)
        article_dict.pop("page_url")
    return [article_dict]


async def make_requests(
    coro: Callable[
        [aiohttp.ClientSession, dict], Coroutine[Any, Any, list[dict[str, Any]]]
    ],
    parameters: Iterable[dict],
    concurrency_limit: int,
    table_handler: TableHandler,
    **kwargs: Any,
) -> tuple[int, list[dict]]:
    """
    Make asynchronous requests using a given coroutine and its parameters.

    The results are written synchronously in batches to an SQLite Database.

    Parameters
    ----------
    coro : callable
        The async function.
        One of compile_page_urls, compile_article_urls, compile_article_data.
    parameter : iterable[dict]
        An iterable with the parameters for the coroutine.
    concurrency_limit : int
        Number of maximum concurrent requests.
    table_handler : TableHandler
        Instance of a TableHandler class that can write the results to SQLite
        database.
    **kwargs : any
        Additional keyword parameters for retry().

    Returns
    -------
    tuple[int, list]
        A tuple containing:
        1. Number of succeeded requests.
        2. List of parameters whose request failed.

    Examples
    --------
    >>> urls = [
    ...     "http://example.com/category1",
    ...     "http://example.com/category2"
    ... ]
    >>> succeeded, failed = await make_requests(get, urls)
    """
    results = []
    failed = []
    succeeded = 0
    semaphore = asyncio.Semaphore(concurrency_limit)

    async def _semaphore_coroutine(params: dict) -> list[dict[str, Any]]:
        async with semaphore:
            return await retry(sessioned_coro, params, **kwargs)

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        sessioned_coro: Callable[
            [dict], Coroutine[Any, Any, list[dict[str, Any]]]
        ] = partial(coro, session)
        pending_tasks = set(
            [asyncio.create_task(_semaphore_coroutine(params)) for params in parameters]
        )
        while pending_tasks:
            done, pending_tasks = await asyncio.wait(
                pending_tasks, return_when=asyncio.FIRST_COMPLETED
            )
            for task in done:
                if task.exception() is not None:
                    task_exception = task.exception()
                    if isinstance(task_exception, TooManyRetries):
                        failed.append(task_exception.params)
                else:
                    results.append(task.result())
                    # write to database if results is larger than BATCH_SIZE
                    if len(results) >= BATCH_SIZE:
                        table_handler.insert_into(flatten(results))
                        # update the counter of successful requests
                        succeeded += len(results)
                        # empty the list of results
                        results.clear()
    # handle any remaining data that either didn't reach BATCH_SIZE
    if len(results) > 0:
        table_handler.insert_into(flatten(results))
        # update the counter of successful requests one last time
        succeeded += len(results)
    return succeeded, failed

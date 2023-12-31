# ecommerce-scraping

Application to scrape products data from an e-commerce website[^1].

I used this application to get descriptions, tags, colours, materials and images (URLs) for more than 135,000 products in 4 hours.[^2]

The application uses `asyncio` and `aiohttp` to handle asynchronous requests and `SQLite3` to write data to a local database.

# Usage

```
$ ./main.py
2023-09-10 13:44:46.861 | INFO     | __main__:scrape_ecommerce_site:21 - [1/4] Getting categories URLs...
2023-09-10 13:44:47.152 | SUCCESS  | __main__:scrape_ecommerce_site:25 - [1/4] Completed
2023-09-10 13:44:47.152 | INFO     | __main__:scrape_ecommerce_site:27 - [2/4] Getting pages URLs...
2023-09-10 13:44:51.753 | SUCCESS  | __main__:scrape_ecommerce_site:37 - [2/4] Completed
2023-09-10 13:44:51.753 | INFO     | __main__:scrape_ecommerce_site:39 - [3/4] Getting articles URLs...
2023-09-10 13:47:45.411 | SUCCESS  | __main__:scrape_ecommerce_site:50 - [3/4] Completed
2023-09-10 13:47:45.411 | INFO     | __main__:scrape_ecommerce_site:52 - [4/4] Getting articles data...
2023-09-10 17:48:38.825 | SUCCESS  | __main__:scrape_ecommerce_site:63 - [4/4] Completed
$ python
>>> import pandas as pd
>>> from webscraper import TableHandler
>>> TableHandler("articles_data").to_pandas()
           id article_url description  colour       tags  materials images_urls
0        2641  https:...   **** d...    camel  ["that...  ["faux...  ["http...
1        2641  https:...   columb...    green  ["excl...  ["nylo...  ["http...
2        7618  https:...   miss s...   orange  ["mini...  ["brod...  ["http...
3        2641  https:...   bershk...     ecru  ["thro...  ["text...  ["http...
4        7618  https:...   **** d...    black  ["go a...  ["non-...  ["http...
...       ...        ...         ...      ...        ...        ...        ...
135933  26090  https:...   hiit c...    white  ["some...  ["soft...  ["http...
135934  26090  https:...   nike y...      red  ["stre...  ["plai...  ["http...
135935  26090  https:...   nike c...     blue  ["take...  ["plai...  ["http...
135936  26090  https:...   under ...     navy  ["jog ...  ["rips...  ["http...
135937  26090  https:...   nike f...     grey  ["for ...  ["spor...  ["http...

[135938 rows x 7 columns]
```

[^1]: The website used to develop and test this application has been anonymized.
[^2]: With a concurrency limit of 100 requests and a backoff factor of 1 for the retry.

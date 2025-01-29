from crawler import Crawler
import logging
import sys

# --------------- For logs ----------------
open("output/logs.log", "w", encoding="utf-8").close()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="output/logs.log",
)

# --------------- Parameters ----------------
url = "https://web-scraping.dev/products"
max_pages = 50
politeness = 1
priority_word = "product"
user_agent = "*"


if len(sys.argv) > 1 and len(sys.argv[1]) > 10:
    url_to_crawl = sys.argv[1]
else:
    url_to_crawl = url

# --------------- Crawl ----------------
crawler = Crawler(
    url=url_to_crawl,
    max_pages=max_pages,
    politeness=politeness,
    priority_word=priority_word,
    user_agent=user_agent,
)
crawler.crawl()

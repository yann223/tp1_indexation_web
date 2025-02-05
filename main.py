"""This is the main file of the project. It contains the
main menu and the functions to crawl and index the data."""

import logging
import os
from consolemenu import ConsoleMenu
from consolemenu.items import FunctionItem
from crawler.crawler import Crawler
from index.indexer import Indexer

# --------------- For logs ----------------
if not os.path.exists("output"):
    os.makedirs("output")

if not os.path.exists("output/logs"):
    os.makedirs("output/logs")

# --------------- Crawl ----------------
## --------------- Parameters ----------------
URL_TO_CRAWL = "https://web-scraping.dev/products"
MAX_PAGES = 50
POLITENESS = 1
PRIORITY_WORD = "product"
USER_AGENT = "*"


## --------------- Functions ----------------
def crawl_url():
    """
    Crawls a URL and saves the data to a JSON file.
    """
    open("output/logs/logs_crawler.log", "w", encoding="utf-8").close()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filename="output/logs/logs_crawler.log",
    )

    print(f"Started crawling {URL_TO_CRAWL}...")
    logging.info("Started crawling %s...", URL_TO_CRAWL)

    crawler = Crawler(
        url=URL_TO_CRAWL,
        max_pages=MAX_PAGES,
        politeness=POLITENESS,
        priority_word=PRIORITY_WORD,
        user_agent=USER_AGENT,
    )
    crawler.crawl()

# --------------- Index ----------------
## --------------- Functions ----------------
def make_index():
    """
    Creates the indexes.
    """
    open("output/logs/logs_index.log", "w", encoding="utf-8").close()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filename="output/logs/logs_index.log",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logging.getLogger().addHandler(console_handler)

    print("Making indexes...")
    logging.info("Making indexes...")
    index = Indexer("data/products.jsonl")
    index.build_index()
    logging.info("Indexing finished!")


# --------------- Menu ----------------
def create_main_menu():
    """
    Create the main menu with options to crawl a URL and make indexes.
    """
    men = ConsoleMenu("Main Menu", "Choose an action", clear_screen=False)

    crawl_item = FunctionItem("Crawl URL", crawl_url, should_exit=True)
    index_item = FunctionItem("Make Indexes", make_index, should_exit=True)

    men.append_item(crawl_item)
    men.append_item(index_item)

    return men

if __name__ == "__main__":
    menu = create_main_menu()
    menu.show()

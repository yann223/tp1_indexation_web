from urllib import robotparser, parse
from bs4 import BeautifulSoup
from collections import deque
import logging
import requests
import time
import json


class Crawler:
    """
    A web crawler that navigates through a site, extracts content from pages, 
    and stores results for further analysis. The crawler respects the site's 
    robots.txt file and allows crawling of a limited number of pages.

    Attributes:
        url (str): The base URL to start crawling from.
        max_pages (int): The maximum number of pages to crawl. Default is 50.
        pages_visited (int): Counter for the number of pages that have been crawled.
        visited_urls (set): A set of URLs that have been crawled to avoid revisiting.
        priority_word (str): A keyword to prioritize certain links for crawling. Default is 'product'.
        queue (deque): A queue of URLs to crawl next.
        parser (RobotFileParser): A robot file parser for checking crawl permissions.
        politeness (int): Delay in seconds between requests to avoid overloading the server.

    Methods:
        crawl(): Starts the crawling process, visiting pages, extracting content, 
                 and adding links to the crawl queue.
        is_allowed_to_crawl(robots_url): Checks if the URL is allowed to be crawled based on robots.txt.
        parse_html(url): Parses the HTML content of a URL and returns a BeautifulSoup object.
        extract_page_content(url): Extracts the title, first paragraph, and internal links of a page.
        save_results(results): Saves the crawled data to a JSON file.
    """
    def __init__(self, url, max_pages=50, politeness=1, priority_word='product'):
        self.url = url
        self.max_pages = max_pages
        self.pages_visited = 0
        self.visited_urls = set()
        self.priority_word = priority_word
        self.queue = deque([url])

        self.parser = robotparser.RobotFileParser()
        self.parser.set_url(url + '/robots.txt')
        self.parser.read()
        self.politeness = self.parser.crawl_delay('*') if self.parser.crawl_delay('*') else politeness
    

    def crawl(self):
        """
        Starts the crawling process, visiting pages, extracting content, 
        and adding links to the crawl queue. It stops when the maximum 
        page limit is reached or all pages are visited.

        The method performs the following:
            - Checks if the URL is allowed to crawl according to robots.txt.
            - Extracts content from each page (title, first paragraph, and links).
            - Prioritizes URLs containing the priority_word for crawling.
            - Sleeps for the defined politeness delay between requests.
            - Saves the results to a JSON file after crawling.

        Returns:
            None
        """
        if not self.is_allowed_to_crawl(self.url):
            logging.error('Not allowed to crawl')
            return None
        
        results = []

        while self.queue and self.pages_visited < self.max_pages:
            url = self.queue.popleft()

            if url in self.visited_urls:
                continue
            
            logging.info(f'Crawling page {self.pages_visited + 1}/{self.max_pages}: {url}')

            content = self.extract_page_content(url)

            if content:
                results.append(content)
                self.pages_visited += 1
                self.visited_urls.add(url)

                priority_links = [link for link in content['links'] if self.priority_word in link]
                other_links = [link for link in content['links'] if self.priority_word not in link]

                self.queue.extend(priority_links + other_links)

            time.sleep(self.politeness)
        
        self.save_results(results)
        logging.info('Crawling complete')
    

    def is_allowed_to_crawl(self, robots_url):
        """
        Checks if the given URL is allowed to be crawled based on the site's robots.txt file.

        Args:
            robots_url (str): The URL of the page to check for crawling permission.

        Returns:
            bool: True if the URL can be crawled, False otherwise.
        """
        return self.parser.can_fetch('*', robots_url)
    

    def parse_html(self, url):
        """
        Parses the HTML content of a given URL and returns a BeautifulSoup object.

        Args:
            url (str): The URL to fetch and parse HTML content from.

        Returns:
            BeautifulSoup: A BeautifulSoup object containing the parsed HTML content.
        """
        response = requests.get(url)
        if response.status_code != 200:
            logging.error('Failed to parse HTML')
            return None
        
        return BeautifulSoup(response.text, 'html.parser')
    

    def extract_page_content(self, url):
        """
        Extracts and returns the title, first paragraph, and internal links from a page.

        Args:
            url (str): The URL of the page to extract content from.

        Returns:
            dict: A dictionary containing the page's title, URL, first paragraph, 
                  and a list of internal links.
        """

        soup = self.parse_html(url)

        title = soup.title.string if soup.title else 'No Title'
        first_paragraph = soup.p.text if soup.p else 'No Paragraph'
        links = [parse.urljoin(url, link['href']) for link in soup.find_all('a', href=True)]
        links = list(set(links))

        content  = {
            'title': title,
            'url': url,
            'first_paragraph': first_paragraph,
            'links': links
        }
        return content
    

    def save_results(self, results):
        """
        Saves the crawled data to a JSON file.

        Args:
            results (list): A list of dictionaries containing the crawled data.

        Returns:
            None
        """
        with open('output/results.json', 'w') as f:
            json.dump(results, f, indent=4)
        logging.info('Results saved to output/results.json')
        

if __name__ == '__main__':
    open("output/logs.log", "w").close()
    logging.basicConfig(
        level=logging.INFO, 
        format="%(asctime)s - %(levelname)s - %(message)s",
        filename="output/logs.log")

    crawler = Crawler('https://web-scraping.dev/products')
    crawler.crawl()
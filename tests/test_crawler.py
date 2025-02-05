"""Tests for the Crawler class and its methods."""

import requests_mock
from bs4 import BeautifulSoup
from crawler.crawler import Crawler


def test_is_allowed_to_crawl():
    """
    Test the `is_allowed_to_crawl` method to ensure it correctly determines if a URL 
    is allowed to be crawled according to the robots.txt settings.

    Asserts:
        - The method returns `True` when a URL is allowed to be crawled.
    """
    crawler = Crawler("https://example.com")

    assert crawler.is_allowed_to_crawl("https://example.com/allowed-page") is True



def test_is_not_allowed_to_crawl():
    """
    Test the `is_allowed_to_crawl` method to ensure it correctly returns `False` 
    when a URL is not allowed to be crawled based on robots.txt.

    This test uses yahoo.com's robots.txt and a disallowed user-agent

    Asserts:
        - The method returns `False` when a URL is disallowed from crawling.
    """
    crawler = Crawler("https://yahoo.com", user_agent="YouBot")

    assert crawler.is_allowed_to_crawl("https://yahoo.com/oui") is False


def test_parse_html():
    """
    Test the `parse_html` method to verify that it correctly parses HTML content 
    and returns a BeautifulSoup object.

    This test uses a mocked HTTP response with a sample HTML content and checks 
    if the title and first paragraph are correctly parsed.

    Asserts:
        - The parsed content is an instance of BeautifulSoup.
        - The title of the page matches the expected value.
        - The first paragraph's text matches the expected value.
    """
    crawler = Crawler("https://example.com")

    html = "<html><head><title>Test Page</title></head><body><p>Hello World</p></body></html>"

    with requests_mock.Mocker() as m:
        m.get("https://example.com", text=html)
        soup = crawler.parse_html("https://example.com")

        assert isinstance(soup, BeautifulSoup)
        assert soup.title.string == "Test Page"
        assert soup.p.text == "Hello World"


def test_extract_page_content():
    """
    Test the `extract_page_content` method to ensure it correctly extracts the title, 
    first paragraph, and internal links from a page's HTML content.

    This test uses mocked HTML content and verifies that the extracted data matches 
    the expected values for the title, first paragraph, and links.

    Asserts:
        - The title of the page is extracted correctly.
        - The first paragraph's content is extracted correctly.
        - Internal and external links are correctly extracted and formatted.
    """
    crawler = Crawler("https://example.com")

    html = """
    <html><head><title>Test Page</title></head>
    <body>
        <p>First paragraph</p>
        <a href="/link1">Link 1</a>
        <a href="https://external.com">External Link</a>
    </body>
    </html>
    """

    with requests_mock.Mocker() as m:
        m.get("https://example.com", text=html)
        content = crawler.extract_page_content("https://example.com")

        assert content["title"] == "Test Page"
        assert content["first_paragraph"] == "First paragraph"
        assert "https://example.com/link1" in content["links"]
        assert "https://external.com" in content["links"]

"""Tests for the Indexer class and its methods."""

from index.indexer import Indexer


def test_extract_variant():
    """Tests extracting a variant from a URL."""
    url = "https://example.com/product?id=123&variant=456"
    indexer = Indexer("data/products.jsonl")

    assert indexer.extract_variant(url) == "456"


def test_tokenize():
    """Tests the tokenize method."""
    text = "Hello, world! This is a beautiful and magnificent test."
    indexer = Indexer("data/products.jsonl")

    tokens = indexer.tokenize(text)
    assert tokens == ["beautiful", "magnificent"]


def test_tokenize_with_positions():
    """Tests the tokenize_with_positions method."""
    text = "Hello world incredible test"
    indexer = Indexer("data/products.jsonl")

    tokens = indexer.tokenize_with_positions(text)
    assert tokens == [(2, "incredible")]


def test_build_reviews_index():
    """Tests building the reviews index."""
    indexer = Indexer("data/products.jsonl")
    indexer.parse_jsonl()
    index = indexer.build_reviews_index()
    url = "https://web-scraping.dev/product/1"

    assert url in index
    assert index[url]["total_reviews"] == 5
    assert index[url]["average_rating"] == 4.6
    assert index[url]["last_rating"] == 4


def test_build_features_index():
    """Tests building the features index."""
    indexer = Indexer("data/products.jsonl")
    indexer.parse_jsonl()
    index = indexer.build_features_index("brand")
    brand = "chocodelight"

    assert brand in index

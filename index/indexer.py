"""This module provides an Indexer class for indexing product data from a JSONL file."""

import json
import logging
import string
import re
import os
from collections import defaultdict
from datetime import datetime
from index.product import Product


class Indexer:
    """
    A class for indexing product data from a JSONL file.

    This class processes product information, builds various indices, and saves them as JSON files.
    It includes functionality for tokenization, extracting variants, and constructing indices for
    reviews, features, titles, and descriptions.

    Attributes:
        STOPWORDS (set): A set of common words to ignore during tokenization.
        jsonl_file (str): The path to the JSONL file containing product data.
        products_list (list): A list of `Product` objects parsed from the JSONL file.

    Methods:
        build_index():
            Builds and saves various indices, including reviews, features,
            title, and description indices.

        parse_jsonl():
            Parses the JSONL file and initializes `Product` objects.

        extract_variant(url: str) -> str | None:
            Extracts the variant identifier from a product URL.

        tokenize(text: str) -> list:
            Tokenizes a given text string, removing punctuation and stopwords.

        tokenize_with_positions(text: str) -> list:
            Tokenizes text while keeping track of token positions.

        build_reviews_index() -> dict:
            Builds an index for product reviews, including total reviews,
            average rating, and last rating.

        build_features_index(feature: str) -> dict:
            Builds an index for specific product features.

        build_title_positional_index() -> dict:
            Constructs a positional index for product titles.

        build_desc_positional_index() -> dict:
            Constructs a positional index for product descriptions.

        save_index_to_json(index: dict, filename: str = "index.json"):
            Saves an index as a JSON file in the output directory.
    """

    STOPWORDS = set()
    with open("data/stopwords-en.txt", "r", encoding="utf-8") as file:
        for line in file:
            STOPWORDS.add(line.strip())

    def __init__(self, jsonl_file):
        self.jsonl_file = jsonl_file
        self.products_list = []

    def build_index(self):
        """
        Builds various indexes for product data, including reviews,
        features, title, and description.
        """
        self.parse_jsonl()
        features_list = ["brand", "made in", "material", "colors"]

        if not os.path.exists("output/indexes"):
            os.makedirs("output/indexes")

        if not os.path.exists("output/indexes/review"):
            os.makedirs("output/indexes/review")

        if not os.path.exists("output/indexes/title"):
            os.makedirs("output/indexes/title")

        if not os.path.exists("output/indexes/description"):
            os.makedirs("output/indexes/description")

        if not os.path.exists("output/indexes/feature"):
            os.makedirs("output/indexes/feature")

        index = self.build_reviews_index()
        self.save_index_to_json(index, "review/reviews_index.json")
        logging.info("Index saved to output/indexes/review/reviews_index.json")

        for feature in features_list:
            index = self.build_features_index(feature)
            self.save_index_to_json(index, f"feature/{feature}_index.json")
            logging.info("Index saved to output/indexes/feature/%s_index.json", feature)

        index = self.build_title_positional_index()
        self.save_index_to_json(index, "title/title_positional_index.json")
        logging.info("Index saved to output/indexes/title/title_positional_index.json")

        index = self.build_desc_positional_index()
        self.save_index_to_json(index, "description/description_positional_index.json")
        logging.info(
            "Index saved to output/indexes/description/description_positional_index.json"
        )

    def parse_jsonl(self):
        """
        Parses the JSONL file and stores product data in the products_list.
        """
        with open(self.jsonl_file, "r", encoding="utf-8") as file:
            for line in file:
                json_line = json.loads(line)
                product = Product(json_line)
                product.set_variant(self.extract_variant(product.id))
                self.products_list.append(product)
                logging.info("Product %s added to the index.", product.title)

    def extract_variant(self, url):
        """
        Extracts the variant parameter from a URL.

        Args:
            url (str): The URL to extract the variant from.

        Returns:
            str or None: The extracted variant if present, otherwise None.
        """
        match = re.search(r"variant=([^&]+)", url)
        if match:
            return match.group(1)
        return None

    def extract_product_id(url):
        """
        Extracts the id number from a URL.

        Args:
            url (str): The URL to extract the id number from.

        Returns:
            int or None: The id number if present, otherwise None.
        """
        match = re.search(r'/product/(\d+)', url)
        if match:
            return match.group(1)
        return None

    def tokenize(self, text):
        """
        Tokenizes the given text by removing punctuation and stopwords.

        Args:
            text (str): The input text to tokenize.

        Returns:
            list: A list of filtered tokens.
        """
        text = text.lower()
        text = re.sub(r"[" + re.escape(string.punctuation) + "]", "", text)

        tokens = text.split()
        tokens = [token for token in tokens if token not in Indexer.STOPWORDS]
        return tokens

    def tokenize_with_positions(self, text):
        """
        Tokenizes the given text while preserving token positions.

        Args:
            text (str): The input text to tokenize.

        Returns:
            list: A list of tuples where each tuple contains the token index and the token itself.
        """
        text = text.lower()
        text = re.sub(r"[" + re.escape(string.punctuation) + "]", "", text)

        tokens = text.split()
        indexed_tokens = list(enumerate(tokens))

        filtered_tokens = [
            (index, token)
            for index, token in indexed_tokens
            if token not in Indexer.STOPWORDS
        ]

        return filtered_tokens

    def build_reviews_index(self):
        """
        Builds an index for product reviews, including total reviews,
        average rating, and last rating.

        Returns:
            dict: A dictionary mapping product IDs to review statistics.
        """
        products_list = self.products_list
        reviews_index = {}
        for product in products_list:
            product_id = product.id
            reviews = product.product_rewiews
            if not reviews:
                reviews_index[product_id] = {
                    "total_reviews": 0,
                    "average_rating": None,
                    "last_rating": None,
                }
            else:
                total = len(reviews)
                avg = sum(review.get("rating", 0) for review in reviews) / total

                reviews_sorted = sorted(
                    reviews, key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d")
                )
                last_rating = reviews_sorted[-1].get("rating", None)
                reviews_index[product_id] = {
                    "total_reviews": total,
                    "average_rating": avg,
                    "last_rating": last_rating,
                }
        return reviews_index

    def build_features_index(self, feature):
        """
        Builds an index for a given product feature.

        Args:
            feature (str): The feature name to index.

        Returns:
            dict: A dictionary mapping feature tokens to product IDs.
        """
        products_list = self.products_list
        features_index = defaultdict(set)
        for product in products_list:
            product_id = product.id
            features = product.product_features
            for feature_name, value in features.items():
                if not isinstance(value, str):
                    continue
                if feature_name == feature:
                    token = value.lower()
                    features_index[token].add(product_id)

        features_index = {token: list(ids) for token, ids in features_index.items()}
        return features_index

    def build_title_positional_index(self):
        """
        Builds a positional index for product titles.

        Returns:
            dict: A dictionary mapping tokens to product IDs and their positions.
        """
        products_list = self.products_list
        index = defaultdict(lambda: defaultdict(list))
        for product in products_list:
            product_id = product.id
            title = product.title
            positions_tokens = self.tokenize_with_positions(title)
            for pos, token in positions_tokens:
                if pos not in index[token][product_id]:
                    index[token][product_id].append(pos)
        positional_index = {}
        for token, doc_positions in index.items():
            positional_index[token] = dict(doc_positions.items())
        return positional_index

    def build_desc_positional_index(self):
        """
        Builds a positional index for product descriptions.

        Returns:
            dict: A dictionary mapping tokens to product IDs and their positions.
        """
        products_list = self.products_list
        index = defaultdict(lambda: defaultdict(list))
        for product in products_list:
            product_id = product.id
            desc = product.description
            positions_tokens = self.tokenize_with_positions(desc)
            for pos, token in positions_tokens:
                if pos not in index[token][product_id]:
                    index[token][product_id].append(pos)
        positional_index = {}
        for token, doc_positions in index.items():
            positional_index[token] = dict(doc_positions.items())
        return positional_index

    def save_index_to_json(self, index, filename="index.json"):
        """
        Saves the index to a JSON file.

        Args:
            index (dict): The index data to save.
            filename (str): The output filename.
        """
        with open(f"output/indexes/{filename}", "w", encoding="utf-8") as file:
            json.dump(index, file, indent=4)

    def load_index_from_json(self, filename="index.json"):
        """
        Loads an index from a JSON file.

        Args:
            filename (str): The input filename.

        Returns:
            dict: The loaded index data.
        """
        with open(f"output/indexes/{filename}", "r", encoding="utf-8") as file:
            index = json.load(file)
        return index

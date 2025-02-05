"""This module defines the search engine class that allows
to search products based on a query."""

import json
import logging
import re
import math
import nltk
from nltk.corpus import stopwords
from index.indexer import Indexer


class SearchEngine:
    """
    A search engine that allows querying products based on indexed data.

    This class provides methods to:
    - Load and manage multiple indexes (title, description, origin, reviews, etc.).
    - Process search queries, including tokenization and synonym expansion.
    - Filter matching documents using total or partial match strategies.
    - Rank documents using BM25 and a custom scoring function.
    - Execute searches and return ranked results in JSON format.

    Attributes:
        STOPWORDS (list): A list of stopwords used for token filtering.
        DATA_PATH (str): Path to the data directory containing index files.
        indexer (Indexer): An instance of the Indexer class for data parsing and indexing.
        title_index (dict): Inverted index for product titles.
        description_index (dict): Inverted index for product descriptions.
        origin_index (dict): Inverted index for product origins.
        reviews_index (dict): Index containing product review information.
        brand_index (dict): Inverted index for product brands.
        domain_index (dict): Inverted index for product domains.
        origin_synonyms (dict): Dictionary mapping origin-related terms to their synonyms.

    Methods:
        get_matching_docs(query):
            Retrieves matching documents based on the query.
        
        get_custom_score(query, doc_id):
            Computes a custom ranking score for a given document.
        
        rank_docs(query, matching_docs):
            Ranks matching documents using BM25 and custom scoring.
        
        get_doc_length(str):
            Computes the number of tokens in a given string.
        
        get_avg_doc_length(doc_field):
            Computes the average length of documents in a specific field.
        
        get_freq(token, doc_id, doc_field):
            Retrieves the frequency of a token in a specific document field.
        
        compute_bm25(query_tokens, product, doc_field, K1=1.5, B=0.75):
            Computes the BM25 score for a given document and query.
        
        load_indexes():
            Loads all necessary indexes from JSON files.
        
        search(limit=5):
            Executes a search query and returns the top results.
        
        get_token_synonyms(token):
            Retrieves synonyms for a given token.
        
        get_query_tokens_with_synonyms(query):
            Tokenizes the query and expands it with synonyms.
        
        filter_partial_match(query_tokens, index_name):
            Filters documents that contain at least one of the query tokens.
        
        filter_total_match(query_tokens, index_name):
            Filters documents that contain all the query tokens.
        
        save_query_results(query, results):
            Saves the search query results in a JSON file.
    """
    nltk.download("stopwords")

    STOPWORDS = stopwords.words("english")
    DATA_PATH = "data/TP3"

    def __init__(self):
        self.indexer = Indexer(f"{self.DATA_PATH}/rearranged_products.jsonl")
        self.indexer.parse_jsonl()
        self.title_index = None
        self.description_index = None
        self.origin_index = None
        self.reviews_index = None
        self.brand_index = None
        self.domain_index = None
        self.origin_synonyms = None

    def search(self, limit=5):
        """
        Executes a search query, retrieves matching documents, ranks them, and saves the results.

        Args:
            limit (int, optional): The maximum number of top results to return. Default is 5.

        Returns:
            dict: A dictionary containing search results, including metadata and ranked products.
        """
        query = input("Enter your query: ")
        results = {}
        matching_docs = self.get_matching_docs(query)
        nb_docs = len(self.indexer.products_list)
        nb_filtered_docs = len(matching_docs)

        dict_score = self.rank_docs(query, matching_docs)
        ordered_score = dict(
            sorted(dict_score.items(), key=lambda item: item[1], reverse=True)[:limit]
        )

        results["Total number of documents"] = nb_docs
        results["Number of documents after filtering"] = nb_filtered_docs
        results["Products"] = []
        for doc in ordered_score:
            product = self.indexer.get_product_by_id(doc)
            json_prod = product.to_json()
            json_prod["score"] = ordered_score[doc]
            results["Products"].append(json_prod)

        self.save_query_results(query, results)

        return results

    def get_matching_docs(self, query):
        """
        Retrieves the set of documents that match the given query.

        Args:
            query (str): The search query.

        Returns:
            set: A set of document IDs that match the query based on various indexes.
        """
        query_tokens = self.get_query_tokens_with_synonyms(query)
        matching_docs = set()
        for token in query_tokens:
            matching_docs.update(self.filter_total_match([token], "brand"))
            matching_docs.update(self.filter_total_match([token], "origin"))
        matching_docs.update(self.filter_total_match(query_tokens, "origin"))
        matching_docs.update(self.filter_total_match(query_tokens, "domain"))
        matching_docs.update(self.filter_partial_match(query_tokens, "title"))
        matching_docs.update(self.filter_partial_match(query_tokens, "description"))
        return matching_docs

    def get_custom_score(self, query, doc_id):
        """
        Computes a custom score for ranking a document based on various factors.

        Args:
            query (str): The search query.
            doc_id (str): The document ID for which the score is computed.

        Returns:
            float: The computed custom score for the document.
        """
        query_tokens = self.get_query_tokens_with_synonyms(query)
        score = 0

        title_match = sum(
            1
            for token in query_tokens
            if token in self.title_index and doc_id in self.title_index[token]
        )
        desc_match = sum(
            1
            for token in query_tokens
            if token in self.description_index
            and doc_id in self.description_index[token]
        )

        score += (title_match * 2) + desc_match

        review_data = self.reviews_index[doc_id]
        score += review_data["mean_mark"] * 2
        score += math.log(1 + review_data["total_reviews"])

        title_pos_score = 0
        desc_pos_score = 0

        for token in query_tokens:
            if token in self.title_index and doc_id in dict(self.title_index[token]):
                positions = dict(self.title_index[token])[doc_id]
                first_position = min(positions) if positions else 9999
                title_pos_score = 100 / (1 + first_position)
            if token in self.description_index and doc_id in dict(
                self.description_index[token]
            ):
                positions = dict(self.description_index[token])[doc_id]
                first_position = min(positions) if positions else 9999
                desc_pos_score = 100 / (1 + first_position)

        pos_score = title_pos_score * 0.4 + desc_pos_score * 0.6
        score += pos_score

        return score

    def rank_docs(self, query, matching_docs):
        """
        Ranks the documents based on a combination of BM25 and custom scoring.

        Args:
            query (str): The search query.
            matching_docs (set): A set of document IDs that matched the query.

        Returns:
            dict: A dictionary mapping document IDs to their ranking scores.
        """
        query_tokens = self.get_query_tokens_with_synonyms(query)
        scores = {}
        for doc_id in matching_docs:
            product = self.indexer.get_product_by_id(doc_id)
            title_score = self.compute_bm25(query_tokens, product, "title")
            description_score = self.compute_bm25(query_tokens, product, "description")
            origin_score = self.compute_bm25(query_tokens, product, "origin")
            brand_score = self.compute_bm25(query_tokens, product, "brand")
            domain_score = self.compute_bm25(query_tokens, product, "domain")
            bm_25_score = (
                title_score
                + description_score
                + origin_score
                + brand_score
                + domain_score
            )
            custom_score = self.get_custom_score(query, doc_id)
            scores[doc_id] = bm_25_score + math.log(max(0.1, custom_score))
        return scores

    def get_doc_length(self, str):
        """
        Calculates the length of a given string in terms of token count.

        Args:
            str (str): The text whose length needs to be calculated.

        Returns:
            int: The number of tokens in the given string.
        """
        return len(self.indexer.tokenize(str))

    def get_avg_doc_length(self, doc_field):
        """
        Computes the average document length for a given field (title or description).

        Args:
            doc_field (str): The field for which the average document length is computed.
                            Must be "title" or "description".

        Returns:
            float: The average length of the specified field across all documents.

        Raises:
            ValueError: If an invalid `doc_field` is provided.
        """
        list_products = self.indexer.products_list
        avg_len = []

        if doc_field == "title":
            for product in list_products:
                avg_len.append(self.get_doc_length(product.title))
        elif doc_field == "description":
            for product in list_products:
                avg_len.append(self.get_doc_length(product.description))
        else:
            raise ValueError("Invalid index name.")

        return sum(avg_len) / len(avg_len)

    def get_freq(self, token, doc_id, doc_field):
        """
        Gets the frequency of a token in a given document field.

        Args:
            token (str): The token whose frequency is being computed.
            doc_id (str): The document ID.
            doc_field (str): The field to check for token frequency 
                            "title", "description", "origin", "brand", or "domain").

        Returns:
            int: The number of occurrences of the token in the specified field.

        Raises:
            ValueError: If an invalid `doc_field` is provided.
        """
        if doc_field == "title":
            title = self.indexer.get_product_by_id(doc_id).title
            title_tokens = self.indexer.tokenize(title)
            return title_tokens.count(token)
        if doc_field == "description":
            description = self.indexer.get_product_by_id(doc_id).description
            description_tokens = self.indexer.tokenize(description)
            return description_tokens.count(token)
        if doc_field == "origin":
            origin = [
                self.indexer.get_product_by_id(doc_id).product_features["made in"]
            ]
            return origin.count(token)
        if doc_field == "brand":
            brand = [self.indexer.get_product_by_id(doc_id).product_features["brand"]]
            return brand.count(token)
        if doc_field == "domain":
            return 0
        raise ValueError("Invalid document field.")

    def compute_bm25(self, query_tokens, product, doc_field, k1=1.5, b=0.75):
        """
        Computes the BM25 score for a document based on a query.

        Args:
            query_tokens (list): A list of query tokens.
            product (object): The product object containing document information.
            doc_field (str): The field to compute BM25 for ("title", "description",
                            "origin", "brand", or "domain").
            K1 (float, optional): BM25 parameter controlling term frequency saturation.
                                    Default is 1.5.
            B (float, optional): BM25 parameter controlling document length normalization.
                                    Default is 0.75.

        Returns:
            float: The BM25 score for the document.

        Raises:
            ValueError: If an invalid `doc_field` is provided.
        """
        if doc_field == "title":
            index = self.title_index
            doc_length = self.get_doc_length(product.title)
            avg_doc_length = self.get_avg_doc_length("title")
        elif doc_field == "description":
            index = self.description_index
            doc_length = self.get_doc_length(product.description)
            avg_doc_length = self.get_avg_doc_length("description")
        elif doc_field == "origin":
            index = self.origin_index
            doc_length = 1
            avg_doc_length = 1
        elif doc_field == "brand":
            index = self.brand_index
            doc_length = 1
            avg_doc_length = 1
        elif doc_field == "domain":
            index = self.domain_index
            doc_length = 1
            avg_doc_length = 1
        else:
            raise ValueError("Invalid document field.")

        doc_id = product.id
        total_docs = len(self.indexer.products_list)
        score = 0
        for token in query_tokens:
            if token in index and doc_id in index[token]:
                freq = self.get_freq(token, doc_id, doc_field)
                doc_freq = len(index[token])
                idf = math.log((total_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
                numerator = freq * (k1 + 1)
                denominator = freq + k1 * (1 - b + b * (doc_length / avg_doc_length))
                score += idf * (numerator / denominator)
        return score

    def load_indexes(self):
        """
        Loads all indexes from JSON files and stores them in instance variables.

        Logs:
            - Logs success messages if indexes are loaded.
            - Logs error messages if any index file is missing.
        """
        try:
            self.title_index = self.indexer.load_index_from_json(
                f"{self.DATA_PATH}/title_index.json"
            )
            logging.info("Title index loaded.")
        except FileNotFoundError:
            logging.error("Title index not found.")

        try:
            self.description_index = self.indexer.load_index_from_json(
                f"{self.DATA_PATH}/description_index.json"
            )
            logging.info("Description index loaded.")
        except FileNotFoundError:
            logging.error("Description index not found.")

        try:
            self.origin_index = self.indexer.load_index_from_json(
                f"{self.DATA_PATH}/origin_index.json"
            )
            logging.info("Origin index loaded.")
        except FileNotFoundError:
            logging.error("Origin index not found.")

        try:
            self.reviews_index = self.indexer.load_index_from_json(
                f"{self.DATA_PATH}/reviews_index.json"
            )
            logging.info("Reviews index loaded.")
        except FileNotFoundError:
            logging.error("Reviews index not found.")

        try:
            self.brand_index = self.indexer.load_index_from_json(
                f"{self.DATA_PATH}/brand_index.json"
            )
            logging.info("Brand index loaded.")
        except FileNotFoundError:
            logging.error("Brand index not found.")

        try:
            self.domain_index = self.indexer.load_index_from_json(
                f"{self.DATA_PATH}/domain_index.json"
            )
            logging.info("Domain index loaded.")
        except FileNotFoundError:
            logging.error("Domain index not found.")

        try:
            self.origin_synonyms = self.indexer.load_index_from_json(
                f"{self.DATA_PATH}/origin_synonyms.json"
            )
            logging.info("Origin synonyms loaded.")
        except FileNotFoundError:
            logging.error("Origin synonyms not found.")

    def get_token_synonyms(self, token):
        """
        Retrieves all synonyms for a given token using the origin synonyms mapping.

        Args:
            token (str): The token for which synonyms should be retrieved.

        Returns:
            list: A list of synonyms, including the token itself.
        """
        synonyms_mapping = self.origin_synonyms
        token = token.lower()
        tokens = [token]
        if token in synonyms_mapping:
            for syn in synonyms_mapping[token]:
                tokens.append(syn.lower())
        else:
            list_syn = list(synonyms_mapping.values())
            for i in range(len(list_syn)):
                if token in list_syn[i]:
                    tokens.extend(list_syn[i])
                    tokens.append(list(synonyms_mapping.keys())[i])
                    break
        return list(set(tokens))

    def get_query_tokens_with_synonyms(self, query):
        """
        Tokenizes a query and expands it with synonyms.

        Args:
            query (str): The raw search query.

        Returns:
            list: A list of query tokens, including synonyms.
        """
        query_tokens = self.indexer.tokenize(query)
        query_tokens_with_synonym = []
        for token in query_tokens:
            query_tokens_with_synonym.extend(self.get_token_synonyms(token))
        query_tokens = query_tokens_with_synonym

        return query_tokens

    def filter_partial_match(self, query_tokens, index_name):
        """
        Retrieves documents that partially match at least one of the query tokens.

        Args:
            query_tokens (list): A list of query tokens.
            index_name (str): The index to search in ("title", "description", "origin",
                            "reviews", "brand", or "domain").

        Returns:
            set: A set of document IDs that contain at least one of the query tokens.

        Raises:
            ValueError: If an invalid `index_name` is provided.
        """
        matching_docs = set()
        if index_name == "title":
            index = self.title_index
        elif index_name == "description":
            index = self.description_index
        elif index_name == "origin":
            index = self.origin_index
        elif index_name == "reviews":
            index = self.reviews_index
        elif index_name == "brand":
            index = self.brand_index
        elif index_name == "domain":
            index = self.domain_index
        else:
            raise ValueError("Invalid index name.")

        for token in query_tokens:
            if token in index:
                matching_docs.update(index[token])
        return matching_docs

    def filter_total_match(self, query_tokens, index_name):
        """
        Retrieves documents that contain all the query tokens.

        Special Handling:
            - For "origin", it checks for multi-word matches in the index.

        Args:
            query_tokens (list): A list of query tokens.
            index_name (str): The index to search in ("title", "description", "origin",
                        "brand", or "domain").

        Returns:
            set: A set of document IDs that contain all the query tokens.

        Raises:
            ValueError: If an invalid `index_name` is provided.
        """
        matching_docs = None
        if index_name == "title":
            index = self.title_index
        elif index_name == "description":
            index = self.description_index
        elif index_name == "origin":
            index = self.origin_index
        elif index_name == "reviews":
            index = self.reviews_index
        elif index_name == "brand":
            index = self.brand_index
        elif index_name == "domain":
            index = self.domain_index
        else:
            raise ValueError("Invalid index name.")

        if index_name == "origin":
            found_origin = None

            for i in range(len(query_tokens)):
                for j in range(i + 1, len(query_tokens) + 1):
                    phrase = " ".join(query_tokens[i:j])
                    if phrase in index:
                        token_docs = set(index[phrase])
                        if found_origin is None:
                            found_origin = token_docs
                        else:
                            found_origin = found_origin.union(token_docs)

            if found_origin is not None:
                matching_docs = found_origin
                return matching_docs
            return set()

        for token in query_tokens:
            if token in SearchEngine.STOPWORDS:
                continue
            if token in index:
                token_docs = set(index[token])
                if matching_docs is None:
                    matching_docs = token_docs
                else:
                    matching_docs = matching_docs.intersection(token_docs)
            else:
                return set()
        return matching_docs if matching_docs is not None else set()

    def save_query_results(self, query, results):
        """
        Saves the search query results as a JSON file.

        Args:
            query (str): The search query.
            results (dict): The search results containing metadata and ranked products.

        Returns:
            None

        File Output:
            - Saves the results in `output/search/{query}.json`.
        """
        query_f = re.sub("\W+", " ", query)
        query_f = query_f.replace(" ", "_")
        with open(f"output/search/{query_f}.json", "w", encoding="utf-8") as file:
            json.dump(results, file, indent=4)

"""This module defines a product class that represents a product with its features and reviews."""

class Product:
    """
    A class to represent a product.

    Attributes:
        url (str): The URL of the product.
        title (str): The title of the product.
        description (str): The description of the product.
        product_features (list): The features of the product.
        links (list): The links of the product.
        product_reviews (list): The reviews of the product.
        id (int): The ID of the product.
        variant (str): The variant of the product.
    """
    def __init__(self, json_line):
        self.id = json_line["url"]
        self.title = json_line["title"]
        self.description = json_line["description"]
        self.product_features = json_line["product_features"]
        self.links = json_line["links"]
        self.product_rewiews = json_line["product_reviews"]
        self.variant = None

    def set_variant(self, variant: str):
        """
        Set the product variant.
        
        Args:
            variant (str): The product variant.
        
        Returns:
            None
        """
        self.variant = variant

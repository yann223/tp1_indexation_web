# TP Indexation web

Yanis Colléaux

---
## Table of Contents
* [Requirements](#req)
* [TP1: Crawl](#crawl)
* [TP2: Indexes](#index)
    * [Indexes description](#ind_des)
    * [Technical choices](#tech_choices)
* [Tests](#tests)

---

<div id='req'/>

## Requirements

Install requirements:
```
pip install -r requirements.txt
```
---

<div id='crawl'/>

## TP1: Crawl

To start the crawler, use the command below, and select the menu [1] by typing `1` in the console:
```
python main.py
```

You can find the results under `output/crawler/results.json`

You can change the following parameters in the `main.py`:
* url to crawl
* number max of pages to crawl
* delay of politeness
* a priority word included in the links fetched
* the user agent

---

<div id='index'/>

## TP2: Indexes

To create the different indexes, use the command below, and select the menu [2] by typing `2` in the console:
```
python main.py
```

The different indexes created can be found in `output/indexes/FEATURE/FEATURE_index.json`

<div id='ind_des'/>

### Indexes description

Several indexes will be created, as shown below:

#### Title positional index

The title positional index stores, for each token, the list of product IDs along with the positions where the token occurs in the title. For example:

```json
{
    "box": {
        "https://web-scraping.dev/product/1": [
            0
        ],
        "https://web-scraping.dev/product/13": [
            0
        ],
        "https://web-scraping.dev/product/13?variant=cherry-large": [
            0
        ],
        "https://web-scraping.dev/product/13?variant=cherry-medium": [
            0
        ]
    },
    "chocolate": {
        "https://web-scraping.dev/product/1": [
            2
        ],
        "https://web-scraping.dev/product/13": [
            2
        ],
        "https://web-scraping.dev/product/13?variant=cherry-large": [
            2
        ],
        "https://web-scraping.dev/product/13?variant=cherry-medium": [
            2
        ]
    }
}
```

#### Review index

The review index is not inverted. It aggregates review information for each product, including total reviews, average rating, and the rating of the latest review (based on date) for one product id. For example:

```json
{
    "https://web-scraping.dev/product/1": {
        "total_reviews": 5,
        "average_rating": 4.6,
        "last_rating": 4
    },
    "https://web-scraping.dev/product/16": {
        "total_reviews": 4,
        "average_rating": 4.75,
        "last_rating": 5
    }
}
```

#### Feature index

For features (e.g., brand), an inverted index is created where tokens in the feature values map to lists of product IDs. For example, the brand index will look like:

```json
{
    "chocodelight": [
        "https://web-scraping.dev/product/13?variant=orange-medium",
        "https://web-scraping.dev/product/1?variant=orange-medium",
        "https://web-scraping.dev/product/1?variant=cherry-medium"
    ],
    "gamefuel": [
        "https://web-scraping.dev/product/28?variant=six-pack",
        "https://web-scraping.dev/product/17?variant=six-pack",
        "https://web-scraping.dev/product/14"
    ]
}
```

#### Description positional index

The description positional index records the position of each token in the product description along with the product ID. For example:

```json
{
    "wardrobe": {
        "https://web-scraping.dev/product/12": [
            8
        ],
        "https://web-scraping.dev/product/12?variant=darkgrey-medium": [
            8
        ],
        "https://web-scraping.dev/product/20": [
            56
        ],
        "https://web-scraping.dev/product/20?variant=beige-6": [
            56
        ]
    },
    "cat": {
        "https://web-scraping.dev/product/12": [
            11,
            24,
            35,
            100
        ],
        "https://web-scraping.dev/product/12?variant=darkgrey-medium": [
            11,
            24,
            35,
            100
        ]
    }
}
```

<div id='tech_choices'/>

### Technical choices

* **JSON parsing**: Each line of the JSONL file is parsed individually using Python's `json` module.

* **Tokenization**: Simple tokenization is applied based on whitespace splitting. Punctuation is removed and the text is converted to lowercase. Only the features retrieved for the feature indexes are not splitted by whitespaces.

* **Stopwords**: The stopswords used are from the Stopwords English [GitHub repository](https://github.com/stopwords-iso/stopwords-en/blob/master/stopwords-en.txt).

* **Data structures**: Python dictionaries (with `defaultdict` for convenience) are used to build and store the indexes, and a `Product` class has been implemented to work with the parsed objects.

* **Additionnal features**: Along with the brand and the origin of the product, we also retrieved the colors and materials of the different products. If we wish to add more features, we just have to modify the `features_list` in the Indexer class to add the needed features.
---

<div id='tests'/>

## Tests

To run the tests run:
```
pytest tests/
```

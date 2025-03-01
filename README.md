# TP Indexation web

Yanis Colléaux

---
## Table of Contents
* [Requirements](#req)
* [TP1: Crawl](#crawl)
* [TP2: Indexes](#index)
    * [Indexes description](#ind_des)
    * [Technical choices](#tech_choices)
* [TP3: Search engine](#tp3)
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


<div id='tp3'/>

## TP3

To make a search, use the command below, and select the menu [3] by typing `3` in the console:
```
python main.py
```

You can then input your query in the console.

The different query results created can be found in `output/search/QUERY.json`

### Technical choices made

* **Total/partial matches in query**: Since all the words are tokenized in a query, the idea of having total matches with the origins of the products could be quite challenging. Indeed, if my product is from South Africa, we don't want it to be returned when the query only contains "south" or "africa". In the mean time, if we have italy and south africa in the same request, we want product from both countries to be returned. To solve this, we will also be aggregating token next to each other and see if together they match with a location in the origin index.
In that case, the query "South Africa" will be returning products from South Africa, whereas the queries "South" or "Africa" won't. The query "south africa italy" will return products from both South Africa and Italy, while the query "south italy africa" will only return products from italy.
We will return products with total match for the fields `brand` and `origin`, and partial match for the others.
* **Scoring function**: The scoring function of a document relatively to a query is made of a computation between a score from the `bm25` function and a custom score explained below.

$$\begin{align*}
\text{score} &= \text{title-bm25} + \text{description-bm25} + \text{origin-bm25} + \text{brand-bm25} + \text{domain-bm25}\\
&+ \log(\max(0.1, \text{custom-score}))
\end{align*}$$
$$\begin{align*}
\text{custom-score} &= \text{title-match}^2 + \text{desc-match} + \text{mean-review}^2 + \log(1 + \text{nb-reviews})\\
&+ 0.4 \cdot \text{title-pos-score} + 0.6 \cdot \text{desc-pos-score}
\end{align*}$$

* With
    * $q_i$: the i-th token of the query
    * $\text{title-match} = \sum_{i=1}^{n} \textbf{1}_{q_i \in \text{title}}$ : the number of tokens which are in the title of the product
    * $\text{desc-match} = \sum_{i=1}^{n} \textbf{1}_{q_i \in \text{desc}}$ : the number of tokens which are in the description of the product
    * $\text{mean-review}$: the average review of the product
    * $\text{nb-reviews}$: the number of total reviews on the product
    * $\text{title-pos-score} = \sum_{i=1}^{n} \frac{10}{1 + \text{position-title}_{q_i}}$ for $q_i$ in the title
    * $\text{title-desc-score} = \sum_{i=1}^{n} \frac{10}{1 + \text{position-description}_{q_i}}$ for $q_i$ in the description

    As the title is shorter and more indicative of the product, $\text{title-match}$ is squared. The reviews are taken into account with the square of the average review of the product. We use the position of the token to give a bigger score if the token is found early in the title or in the description.
    Regarding the final score, as the custom score can be bigger than the score computed with the `bm25` function, we decided to add the custom score taken to the logarithm to prevent any exponential impact from the custom score, and give more importance to the score computed with the `bm25` function.
* **Search pipeline**: When a query is inputed by the user, the following steps will happen:
    1. Tokenization of the query
    2. Expansion of the tokenization with synonyms
    3. Retrieval of the documents which match the tokens from the query (total or partial match depending on the field)
    4. Retrieval of the metadata (Number of documents before and after filtering)
    5. Computation of the final score for each document relatively to the query
    6. Order the documents with the final score descending

* **BM25 Coefficients**: Here we chose $k_1=1.5$ and $b=0.75$ by default. We judged that the scoring function behaves correctly regarding our expectations and that no optimisation of these coefficients are needed.

### Requests examples

We will show here the metadata of several requests to see how works the search engine under different conditions:

* Request `italy`:
```
{
    "Total number of documents": 156,
    "Number of documents after filtering": 21,
    "Products": [...
    ]
}
```
Here only 21 documents go through the filtering, which matches the number of products from Italy.

* Request `south africa`:
```
{
    "Total number of documents": 156,
    "Number of documents after filtering": 8,
    "Products": [...
    ]
}
```
Here again, only 8 documents, which origin matches with South Africa goes through the filtering.

* Request `italy south africa`:
```
{
    "Total number of documents": 156,
    "Number of documents after filtering": 29,
    "Products": [...
    ]
}
```
Here, 29 products from either Italy or South Africa are returned.

* Request `south italy africa`:
```
{
    "Total number of documents": 156,
    "Number of documents after filtering": 21,
    "Products": [...
    ]
}
```
Here, only the italian products are returned as expected.

Regarding the synonyms, we can test the two following requests:

* Request `usa`:
```
{
    "Total number of documents": 156,
    "Number of documents after filtering": 31,
    "Products": [...
    ]
}
```

* Request `america`:
```
{
    "Total number of documents": 156,
    "Number of documents after filtering": 31,
    "Products": [...
    ]
}
```
This shows us that the expansion of a request with synonyms works well.

* Request `sweet candy box`:
```
{
    "Total number of documents": 156,
    "Number of documents after filtering": 21,
    "Products": [
        {
            "title": "Box of Chocolate Candy",
            "description": "Whether you're looking for the perfect gift or just want to treat yourself, our box of chocolate candy is sure to satisfy. Indulge your sweet tooth with our box of chocolate candy. Choose from a variety of flavors including zesty orange and sweet cherry",
            "url": "https://web-scraping.dev/product/25",
            "score": 16.084055221914465
        },
        {
            "title": "Box of Chocolate Candy",
            "description": "Whether you're looking for the perfect gift or just want to treat yourself, our box of chocolate candy is sure to satisfy. Each box contains an assortment of rich, flavorful chocolates with a smooth, creamy filling. Indulge your sweet tooth with our box of chocolate candy",
            "url": "https://web-scraping.dev/product/1",
            "score": 15.609797961908306
        },
        {
            "title": "Box of Chocolate Candy",
            "description": "Choose from a variety of flavors including zesty orange and sweet cherry. Each box contains an assortment of rich, flavorful chocolates with a smooth, creamy filling. Indulge your sweet tooth with our box of chocolate candy",
            "url": "https://web-scraping.dev/product/13",
            "score": 15.562981963666246
        },
        {
            "title": "Box of Chocolate Candy - Cherry large",
            "description": "Indulge your sweet tooth with our box of chocolate candy. Whether you're looking for the perfect gift or just want to treat yourself, our box of chocolate candy is sure to satisfy. Choose from a variety of flavors including zesty orange and sweet cherry",
            "url": "https://web-scraping.dev/product/1?variant=cherry-large",
            "score": 15.218771407810628
        },
        {
            "title": "Box of Chocolate Candy - Cherry small",
            "description": "Each box contains an assortment of rich, flavorful chocolates with a smooth, creamy filling. Whether you're looking for the perfect gift or just want to treat yourself, our box of chocolate candy is sure to satisfy. Indulge your sweet tooth with our box of chocolate candy",
            "url": "https://web-scraping.dev/product/25?variant=cherry-small",
            "score": 14.91977461122283
        }
    ]
}
```
As expected, the best results are all from the same product (Box of chocolate candy), and all of them contains the word "sweet" in the description.
To analyze things a little further, the three first products have the same title, but not the same descriptions. For the first products, the terms used in the request occur 6 times in the description, making it first of the list. For the second and third products, the terms from the request only occur 5 times in the description, making them have a really close score, which differs only by the position of the releving terms in the description.
The last two products both have 6 occurences of the request terms in their description, but the title is longer than the others, making it having less matching terms in proportion. Since we tend to privilege a matching title when we compute the score, these two products are ranked a little bit worse than the others.

---

<div id='tests'/>

## Tests

To run the tests run:
```
pytest tests/
```

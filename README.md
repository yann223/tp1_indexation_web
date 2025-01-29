# TP1 Indexation web

Yanis Colléaux

## Crawl

Install requirements:
```
pip install -r requirements.txt
```

To start the crawler, use the command below:
```
python main.py
```

or

```
python main.py [your_url]
```

You can find the results under `output/results.json`

You can change the following parameters in the `main.py`:
* url to crawl
* number max of pages to crawl
* delay of politeness
* a priority word included in the links fetched
* the user agent

## Tests

To run the tests run:
```
pytest tests/
```

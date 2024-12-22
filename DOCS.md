# How to Run the Scraper

First, you must sign up to the Bright Data Platform and get the required credentials, (1) Scraping Browser and (2) Scraping API. Then, set the credentials into environment variables so we can reuse it later.

```bash
export BRD_AUTH="brd-customer-XXX-zone-XXX:XXX"
export BRD_API_KEY="xxxxxx"
```

## Scrape LKPP

For LKPP page, I used the Scraping Browser service from Bright Data and I used Playwright to build the scraper.

### Product List Page

Scrape LKPP E-Katalog product listing page based on `category` and `commodity` IDs.

```bash
# scrape using local browser
python scripts/scrape_browser.py --output-file ./data/scraped/lkpp-serp.jsonl lkpp-serp --category 1237626 --commodity 90424 --max-pages 200

# scrape using Bright Data API
python scripts/scrape_browser.py --brd-auth $BRD_AUTH --output-file ./data/scraped/lkpp-serp.jsonl lkpp-serp --category 1237626 --commodity 90424 --max-pages 200
```

### Product Detail Page

Extract URLs from scraped LKPP product listing page.

```bash
cat ./data/scraped/lkpp-serp.jsonl | jq -cr '.product_url' > ./data/inputs/lkpp-urls.txt
```

Scrape LKPP E-Katalog product detail page based on list of URLs.

```bash
python scripts/scrape_browser.py --output-file ./data/scraped/lkpp-products.jsonl lkpp-item --input-file ./data/inputs/lkpp-urls.txt
```

## Scrape Tokopedia/Lazada

For Tokopedia and Lazada, Bright Data provides a convenient service through the Web Scraper API to collect the product information. Before running the scraper, you need to create the search terms first.

Ideally, you would want to extract the search keywords from LKPP E-Katalog products, then save it into a file. In this repo, I demonstrated a simple keyword research using n-gram, available in `notebooks/lkpp-extract-terms.ipynb`.

Use Web Scraper API to scrape data from Tokopedia and Lazada using the specified terms in `terms.txt`. The snapshot file will contain the `snapshot_id` that we will use to download the scraping results.

```bash
python scripts/scrape_api.py --api-key $BRD_API_KEY discover --terms-file ./data/inputs/terms.txt --output-file ./data/inputs/tokopedia-snapshot.jsonl --engine tokopedia
python scripts/scrape_api.py --api-key $BRD_API_KEY discover --terms-file ./data/inputs/terms.txt --output-file ./data/inputs/lazada-snapshot.jsonl --engine lazada
```

Download scraped data from snapshot file.

```bash
python scripts/scrape_api.py --api-key $BRD_API_KEY download --snapshots-file ./data/inputs/tokopedia-snapshot.jsonl  --output-path ./data/scraper-api/tokopedia
python scripts/scrape_api.py --api-key $BRD_API_KEY download --snapshots-file ./data/inputs/lazada-snapshot.jsonl --output-path ./data/scraper-api/lazada
```

Sometimes, the scraping will not succeed or the product has some variants, we can extract those URLs so we can try the scraping again using the data collection API.

```bash
python scripts/scrape_api.py --api-key $BRD_API_KEY extract-extras --output-path ./data/scraper-api/tokopedia --output-file ./data/inputs/extra-urls-tokopedia.txt
python scripts/scrape_api.py --api-key $BRD_API_KEY extract-extras --output-path ./data/scraper-api/lazada --output-file ./data/inputs/extra-urls-lazada.txt
```

Use data collection API to scrape the list of URLs.

```bash
python scripts/scrape_api.py --api-key $BRD_API_KEY collect --urls-file ./data/inputs/extra-urls-tokopedia.txt --output-file ./data/inputs/tokopedia-snapshot-extra.jsonl --engine tokopedia
python scripts/scrape_api.py --api-key $BRD_API_KEY collect --urls-file ./data/inputs/extra-urls-lazada.txt --output-file ./data/inputs/lazada-snapshot-extra.jsonl --engine lazada
```

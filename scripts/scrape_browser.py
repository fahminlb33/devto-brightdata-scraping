import json
import random
import asyncio
import argparse
from typing import Any

import tqdm

from playwright.async_api import Browser, Page
from playwright.async_api import async_playwright


# ========================================================================
#   WEB SCRAPING
# ========================================================================


async def scrape_ekatalog_lkpp_serp(
    category: str, commodity: str, page_offset: int, page: Page
):
    # navigate to catalogue page for Laptops
    url = f"https://e-katalog.lkpp.go.id/productsearchcontroller/listproduk?cat={category}&commodityId={commodity}&order=relevance&limit=12&offset={page_offset}"
    await page.goto(url)

    # wait for navigate to products page
    await page.wait_for_timeout(timeout=5000)

    # find products
    products = await page.locator("//div[@class='card-item card-item-custom']").all()
    for product in products:
        # scroll section
        await product.scroll_into_view_if_needed()

        # extract information
        name = await product.locator("xpath=//a[@data-toggle='tooltip']").get_attribute(
            "title"
        )
        product_url = await product.locator(
            "xpath=//a[@data-toggle='tooltip']"
        ).get_attribute("href")
        image_url = await product.locator(
            'xpath=//img[@alt="E-Katalog LKPP"]'
        ).get_attribute("src")
        details = await product.locator(
            "xpath=//div[@class='card-item-description']"
        ).inner_text()
        tags = await product.locator("xpath=//span").all()

        # yield row
        yield {
            "name": name,
            "tags": [await tag.get_attribute("title") for tag in tags],
            "details": {
                k: v.strip()
                for k, v in zip(
                    [
                        "provider",
                        "tkdn_percentage",
                        "bmp",
                        "tkdn_bmp_score",
                        "price",
                    ],
                    details.split("\n\n"),
                )
            },
            "page": page_offset,
            "category": category,
            "commodity": commodity,
            "product_url": f"https://e-katalog.lkpp.go.id{product_url}",
            "image_url": f"https://e-katalog.lkpp.go.id{image_url}",
            "scrape_url": page.url,
        }


async def scrape_ekatalog_lkpp_item(url: str, page: Page):
    # visit product page
    await page.goto(url)

    # to store product details
    product_spec = {
        "title": await page.locator("xpath=//h2").inner_text(),
        "sku": await page.locator("xpath=//h2/following-sibling::p[1]").inner_text(),
        "price": await page.locator(
            "xpath=//div[@id='detailhargaChange']"
        ).inner_text(),
        "stock": await page.locator(
            "xpath=//h4[@class='col-md-12 float-right']"
        ).inner_text(),
        "tags": await page.locator("xpath=//*[@class='badge']").all_inner_texts(),
        "details": {},
        "url": url,
    }

    # get spec table
    spec_table = await page.locator("xpath=//div[@id='spesifikasi']/div/div").all()
    for row in spec_table:
        # scroll if required
        await row.scroll_into_view_if_needed()

        # parse table row
        title = await row.locator(
            "xpath=//div[@class='detail-heading col-md-2']"
        ).inner_text()
        content = await row.locator(
            "xpath=//div[@class='detail-heading col-md-2']/following-sibling::*[1]"
        ).inner_text()

        # save to details
        product_spec["details"][title.strip()] = content.strip()

    # get if the item has problems
    try:
        product_spec["alerts"] = await page.locator(
            '//div[@id="error-message" and @class="alert alert-warning"]'
        ).inner_text(timeout=5)
    except:
        pass

    return product_spec


# ========================================================================
#  RUNNERS
# ========================================================================


async def run_lkpp_serp(args: dict[str, Any], browser: Browser):
    # create new page
    page = await browser.new_page()

    # open save file
    with open(args["output_file"], "a+") as output_file:
        # process each page
        for page_i in tqdm.tqdm(range(1, args["max_pages"] + 1)):
            # scrape each item
            async for data in scrape_ekatalog_lkpp_serp(
                args["category"], args["commodity"], page_i + 275, page
            ):
                json.dump(data, output_file)
                output_file.write("\n")

            # flush after each page
            output_file.flush()

            # sleep before each fetch
            await asyncio.sleep(random.random() * args["delay"])


async def run_lkpp_item(args: dict[str, Any], browser: Browser):
    # create new page
    page = await browser.new_page()

    # open input and save file
    with (
        open(args["input_file"], "r") as input_file,
        open(args["output_file"], "a+") as output_file,
    ):
        # read each line
        for url in tqdm.tqdm(input_file.readlines()):
            # scrape page
            data = await scrape_ekatalog_lkpp_item(url, page)

            # save to output
            json.dump(data, output_file)
            output_file.write("\n")
            output_file.flush()

            # sleep before each fetch
            await asyncio.sleep(random.random() * args["delay"])


# ========================================================================
#  ENTRY POINT
# ========================================================================


async def main(args: dict[str, Any]):
    print(args)
    async with async_playwright() as p:
        # launch browser
        if args["brd_auth"] is not None and len(args["brd_auth"]) > 10:
            url = f"wss://{args['brd_auth']}@brd.superproxy.io:9222"
            browser = await p.chromium.connect_over_cdp(url, slow_mo=50)
        else:
            browser = await p.chromium.launch(headless=False, slow_mo=50)

        # run
        if args["mode"] == "lkpp-serp":
            await run_lkpp_serp(args, browser)

        elif args["mode"] == "lkpp-item":
            await run_lkpp_item(args, browser)

    await browser.close()


if __name__ == "__main__":
    # --- create main argparser
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-file", type=str, required=True)
    parser.add_argument("--delay", type=int, default=1)
    parser.add_argument("--brd-auth", type=str)

    # --- register subparsers
    subparsers = parser.add_subparsers(dest="mode")

    # LKPP SERP
    lkpp_serp = subparsers.add_parser("lkpp-serp")
    lkpp_serp.add_argument("--category", type=str, required=True)
    lkpp_serp.add_argument("--commodity", type=str, required=True)
    lkpp_serp.add_argument("--max-pages", type=int, required=True)

    # LKPP Detail
    lkpp_item = subparsers.add_parser("lkpp-item")
    lkpp_item.add_argument("--input-file", type=str, required=True)

    # run app
    asyncio.run(main(vars(parser.parse_args())))

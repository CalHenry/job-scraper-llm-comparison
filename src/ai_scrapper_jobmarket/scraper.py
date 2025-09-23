import json
import urllib.parse

import polars as pl
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig

from .cleaners import remove_with_keyword


async def extract_links(job_name: str):
    """
    Extract links of the first page from choisirleservicepublic.gouv.fr (french governement job platform)
    Extract for a specific job keyword (encode it to url)
    Use 'css_selector' to have a specific output (we obtain only links in markdown format)
    Store the list of links to json
    """
    job_name_encoded = urllib.parse.urlencode(job_name)

    # Crawl4ai config
    browser_conf = BrowserConfig(headless=True, text_mode=True)
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        css_selector=".fr-card--offer .fr-card__title a",
        word_count_threshold=5,
    )

    # Scrapping
    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(
            url=f"https://choisirleservicepublic.gouv.fr/nos-offres/filtres/mot-cles/{job_name_encoded}/",
            config=config,
        )

    # save to json
    with open("output/links/frgouv_links.json", mode="w") as file:
        json.dump(result.links["internal"], file)


async def scrape_job_offers(links_file: str):
    """
    Scrappe content of job offers from a list of links in json format
    load the json using polars --> convert to python list
    Use crawl4ai basic web crawler to extract the content with filters:
        - css_selector to only scrappe where the relevant content is
        - exclude_selector to remove unwanted content, captured by css_selector
    Use arun_many() to scrape the links with parallel processing
    Clean the markdown output base on a keyword one more time,
    save the content to results folder as markdown files
    """
    # import links from json
    urls = pl.Series(
        pl.read_json(f"output/links/{links_file}.json").select("href")
    ).to_list()

    # crawl4ai
    browser_config = BrowserConfig(headless=True, text_mode=True)
    crawler_config = CrawlerRunConfig(
        css_selector=".fr-col-12",
        excluded_selector=".fr-breadcrumb, .fr-share",
        exclude_external_links=True,
        exclude_all_images=True,
        word_count_threshold=5,
        cache_mode=CacheMode.BYPASS,
    )

    # Scrapping
    async with AsyncWebCrawler(config=browser_config) as crawler:
        results = await crawler.arun_many(
            urls=urls,
            config=crawler_config,
        )

    # clean and store each job offer to a .md file
    for i, res in enumerate(results):
        if res.success:
            filtered_content = remove_with_keyword(
                res.markdown, "Des offres d'emplois recommandées pour vous"
            )
            with open(f"results/job_{i}.md", "w", encoding="utf-8") as f:
                f.write(filtered_content)
        else:
            print("Failed:", res.url, "-", res.error_message)

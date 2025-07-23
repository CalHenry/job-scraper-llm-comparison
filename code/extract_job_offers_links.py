import asyncio
import json
import urllib.parse

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig


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

    # Sscrapping
    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(
            url=f"https://choisirleservicepublic.gouv.fr/nos-offres/filtres/mot-cles/{job_name_encoded}/",
            config=config,
        )

    # save to json
    with open("output/links/frgouv_links.json", mode="w") as file:
        json.dump(result.links["internal"], file)


if __name__ == "__main__":
    asyncio.run(extract_links())

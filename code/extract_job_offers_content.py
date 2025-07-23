import asyncio

import polars as pl
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig

from ai_scrapper_jobmarket.trim_markdown import remove_with_keyword


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


if __name__ == "__main__":
    asyncio.run(scrape_job_offers())

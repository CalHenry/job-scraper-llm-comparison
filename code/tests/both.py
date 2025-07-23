import asyncio

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig


async def main():
    browser_confing = BrowserConfig()
    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        css_selector=".fr-card--offer .fr-card__title a",
        word_count_threshold=5,
    )

    async with AsyncWebCrawler(config=browser_confing) as crawler:
        result = await crawler.arun(
            url="https://choisirleservicepublic.gouv.fr/nos-offres/filtres/mot-cles/data%20scientist/",
            config=crawler_config,
        )

    links_from_crawling = result.links["internals"]

    #####

    browser_config_2 = BrowserConfig(headless=True, text_mode=True)

    crawler_config_2 = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        css_selector=".fr-col-12",
        excluded_selector=".fr-breadcrumb, .fr-share",
        exclude_external_links=True,
        exclude_all_images=True,
        word_count_threshold=5,
    )

    for link in links_from_crawling:
        async with AsyncWebCrawler(config=browser_config_2) as crawler:
            result = await crawler.arun(
                url=link,
                config=crawler_config_2,
            )

    with open("tenta.md", "w", encoding="utf-8") as f:
        f.write(result.markdown)


if __name__ == "__main__":
    asyncio.run(main())

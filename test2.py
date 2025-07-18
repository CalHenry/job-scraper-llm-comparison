import asyncio

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig

# css selector for the job offer: div.item:nth-child()


async def main():
    browser_conf = BrowserConfig()
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        css_selector="div.item:nth-child(-n+30)",
        word_count_threshold=5,
    )

    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(
            url="https://choisirleservicepublic.gouv.fr/nos-offres/filtres/mot-cles/data%20scientist/",
            config=config,
        )

    with open("output.md", "w", encoding="utf-8") as f:
        f.write(result.markdown)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig


async def main():
    browser_config = BrowserConfig(headless=True, text_mode=True)

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        css_selector=".fr-col-12",
        excluded_selector=".fr-breadcrumb, .fr-share",
        exclude_external_links=True,
        exclude_all_images=True,
        word_count_threshold=5,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://choisirleservicepublic.gouv.fr/offre-emploi/data-scientist---cheffe-de-projet-statistique-dgesip-dgri-a2-reference-2025-1975604/",
            config=crawler_config,
        )

    with open("tenta.md", "w", encoding="utf-8") as f:
        f.write(result.markdown)


if __name__ == "__main__":
    asyncio.run(main())

# test page: https://fr.wikipedia.org/wiki/Jean_Mermoz
# ex result page: https://choisirleservicepublic.gouv.fr/nos-offres/filtres/mot-cles/data%20scientist/
# ex job page: https://choisirleservicepublic.gouv.fr/offre-emploi/data-scientist---cheffe-de-projet-statistique-dgesip-dgri-a2-reference-2025-1975604/
# div.strate: nth - child(8)

import asyncio

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig


async def main():
    browser_conf = BrowserConfig()
    config = CrawlerRunConfig(
        excluded_tags=["header", "footer", "aside"],
        exclude_external_links=True,
        # word_count_threshold=5,
        cache_mode=CacheMode.BYPASS,
    )

    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(
            url="https://choisirleservicepublic.gouv.fr/offre-emploi/data-scientist---cheffe-de-projet-statistique-dgesip-dgri-a2-reference-2025-1975604/",
            config=config,
        )

    with open("job_page.md", "w", encoding="utf-8") as f:
        f.write(result.markdown)


if __name__ == "__main__":
    asyncio.run(main())

# test page: https://fr.wikipedia.org/wiki/Jean_Mermoz
# ex result page: https://choisirleservicepublic.gouv.fr/nos-offres/filtres/mot-cles/data%20scientist/
# ex job page: https://choisirleservicepublic.gouv.fr/offre-emploi/data-scientist---cheffe-de-projet-statistique-dgesip-dgri-a2-reference-2025-1975604/
# div.strate: nth - child(8)


# Script for a job page


import asyncio

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


async def main():
    prune_filter = PruningContentFilter(
        # Lower → more content retained, higher → more content pruned
        threshold=0.50,
        # "fixed" or "dynamic"
        threshold_type="dynamic",
        # min_word_threshold=5,
    )

    # Step 2: Insert it into a Markdown Generator
    md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)

    browser_conf = BrowserConfig()
    config = CrawlerRunConfig(
        excluded_tags=["header", "footer", "aside"],
        exclude_external_links=True,
        # word_count_threshold=5,
        cache_mode=CacheMode.BYPASS,
        markdown_generator=md_generator,
    )

    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(
            url="https://choisirleservicepublic.gouv.fr/offre-emploi/data-scientist---cheffe-de-projet-statistique-dgesip-dgri-a2-reference-2025-1975604/",
            config=config,
        )

    with open("job_page_fit.md", "w", encoding="utf-8") as f:
        f.write(result.markdown.fit_markdown)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio

import nest_asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import (
    DomainFilter,
    FilterChain,
    URLPatternFilter,
)
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

nest_asyncio.apply()


async def advanced_crawler():
    filter_chain = FilterChain(
        [
            URLPatternFilter(patterns=["*offre-emploi*"]),
            DomainFilter(
                allowed_domains=["choisirleservicepublic.gouv.fr"],
            ),
        ]
    )

    strategy = BFSDeepCrawlStrategy(
        max_depth=2,
        include_external=False,
        max_pages=11,  # 10 offers + the main page
        filter_chain=filter_chain,
    )

    prune_filter = PruningContentFilter(
        # Lower → more content retained, higher → more content pruned
        threshold=0.50,
        threshold_type="dynamic",
    )

    md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)

    browser_conf = BrowserConfig()
    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        exclude_external_links=True,
        cache_mode=CacheMode.BYPASS,
        markdown_generator=md_generator,
    )

    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(
            url="https://choisirleservicepublic.gouv.fr/nos-offres/filtres/mot-cles/data%20scientist/",
            config=config,
        )

    for i, result in enumerate(result):
        with open(f"results/result_{i}.md", "w", encoding="utf-8") as f:
            f.write(str(result.markdown.fit_markdown))


if __name__ == "__main__":
    asyncio.run(advanced_crawler())

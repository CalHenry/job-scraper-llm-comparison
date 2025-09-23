import asyncio

import nest_asyncio
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    LLMConfig,
    LLMContentFilter,
)
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

    ollama_config = LLMConfig(
        provider="ollama/qwen3:4b", base_url="http://localhost:11434"
    )

    filter = LLMContentFilter(
        llm_config=ollama_config,
        instruction="""
        This is a job offer page. Focus on extractiing the main elements with their headers
        Include:
        - information about the missions
        - Essential details
        Exclude:
        - other job offer
        - irrelevant text
        - links, images
        Format the output as clean markdown with proper headers.
        """,
        chunk_token_threshold=500,
        verbose=True,
    )

    md_generator = DefaultMarkdownGenerator(content_filter=filter)

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

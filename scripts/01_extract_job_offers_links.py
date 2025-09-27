import asyncio

from src.ai_scrapper_jobmarket.scraper import extract_links

if __name__ == "__main__":
    asyncio.run(extract_links(job_name="data scientist"))

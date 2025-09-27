import asyncio

from src.ai_scrapper_jobmarket.scraper import scrape_job_offers

if __name__ == "__main__":
    asyncio.run(scrape_job_offers(links_file_name="clsp_links"))

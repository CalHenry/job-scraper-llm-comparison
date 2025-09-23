from src.ai_scrapper_jobmarket.llm_processor import (
    process_markdown_files,
)


def main():
    # Configuration
    input_directory = "outputs/scraping_results"
    output_directory = "outputs/json_files/llm_output"

    # Process all files delay between files
    metadata = process_markdown_files(
        input_dir=input_directory,
        output_dir=output_directory,
        delay_seconds=5.0,
    )
    print("job's done")
    return metadata


# Run the processing
if __name__ == "__main__":
    metadata = main()

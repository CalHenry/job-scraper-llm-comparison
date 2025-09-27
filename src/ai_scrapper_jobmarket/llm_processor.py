import time
from pathlib import Path
from typing import Dict, List

from src.ai_scrapper_jobmarket.langchain import extraction_chain
from src.ai_scrapper_jobmarket.models import ExtractedContent


def read_markdown_file(file_path: str) -> str:
    """Read a single markdown file and return its content."""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def remove_punct_and_newlines(text):
    """
    Removes newlines and punctuation from markdown content while preserving headers on their own lines.
    LLM are sensible to text structures and formating elements can be understood as end of content.
    Critical for LLMs to accurately process and interpret the content without missing context.
    """
    # remove punct
    to_remove = [
        "-",
        "...",
        ".",
        ";",
        ":",
        "*",
        "•",
        "Afficher la suite",
        "Missions",
        "Activités principales",
    ]  # we also remove some sturcture elements that the model can interpret as another section

    for item in to_remove:
        text = text.replace(item, "")

    lines = text.strip().split("\n")
    result = []
    content_lines = []  # store non headers lines

    # removes newlines and preserve the headers in their own line
    for line in lines:
        line = line.strip()
        if line.startswith("#"):
            # Join any accumulated content and add it
            if content_lines:
                result.append(" ".join(content_lines))
                content_lines = []
            # Add the header
            result.append(line)
        elif line:  # for any remaining lines
            content_lines.append(line)

    # Add any remaining content
    if content_lines:
        result.append(" ".join(content_lines))

    return "\n\n".join(result)


def extract_content(document: str) -> dict:
    """Extract structured content from document using LLM."""
    json_schema = (ExtractedContent.model_json_schema(),)
    raw_response = extraction_chain.invoke(input=document, json_schema=json_schema)
    job_data = ExtractedContent.model_validate_json(raw_response)
    return job_data


def process_markdown_files(
    input_dir: str, output_dir: str, delay_seconds: float = 10.0
) -> List[Dict]:
    """
    Process all markdown files in a directory one at a time.
    """
    # Setup paths
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Get all markdown files
    md_files = list(input_path.glob("*.md"))

    print(f"Found {len(md_files)} files to process")

    metadata = []

    # Process each file individually
    for i, md_file in enumerate(md_files, 1):
        try:
            print(f"Processing {i}/{len(md_files)}: {md_file.name}")
            start_time = time.time()

            # Read the markdown file
            document_content = read_markdown_file(md_file)
            # prepare for llm
            document_content_compact = remove_punct_and_newlines(document_content)
            # document_content_compact = document_content

            # prepare for langchain
            document = {"document": document_content_compact}

            # Extract content using LLM
            extracted_content = extract_content(document)

            # Generate output filename (replace .md with .json)
            output_filename = md_file.stem + ".json"
            output_file_path = output_path / output_filename

            # Save to JSON
            with open(output_file_path, "w", encoding="utf-8") as file:
                file.write(extracted_content.model_dump_json(indent=2))

            processing_duration = time.time() - start_time

            metadata.append(
                {
                    "input_file": str(md_file),
                    "output_file": str(output_file_path),
                    "status": "success",
                    "duration_seconds": round(processing_duration, 2),
                }
            )
            print(f"✅ Successfully processed {md_file.name} -> {output_filename}")

            # delay to be gentle with the hardware
            if delay_seconds > 0 and i < len(
                md_files
            ):  # Don't delay after the last file
                time.sleep(delay_seconds)

        except Exception as e:
            error_msg = f"Error processing {md_file.name}: {str(e)}"
            print(f"❌ {error_msg}")

            metadata.append(
                {
                    "input_file": str(md_file),
                    "output_file": None,
                    "status": "error",
                    "error": str(e),
                    "duration_seconds": round(processing_duration, 2),
                }
            )
            # Continue with next file even if fails
            continue

    return metadata

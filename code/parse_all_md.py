import time
from pathlib import Path
from typing import Dict, List, Optional

from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_ollama.llms import OllamaLLM
from pydantic import BaseModel, Field


# Pydantic model
class ExtractedContent(BaseModel):
    title: Optional[str] = Field(
        default=None,
        description="Title of the document, this is the line of the document and the first markdown header with a single #",
    )
    ref: Optional[str] = Field(
        default=None,
        description="Reference of the page, number in 2 parts with a dash - and number. After the keyword: Référence",
    )
    employeur_name: Optional[str] = Field(
        default=None,
        description="Name entity who hires, can be an acronym. After the keyword: Employeur",
    )
    loc: Optional[str] = Field(
        default=None, description="address. After the keyword: Localisation"
    )
    experience: Optional[str] = Field(
        default=None, description="After the keywords: Expérience souhaitée"
    )
    cat: Optional[str] = Field(default=None, description="After the keyword: Catégorie")
    remote: Optional[str] = Field(
        default=None,
        description="Remote working. After the keywords: Télétravail possible",
    )
    missions: Optional[str] = Field(
        default=None,
        description="Description of the missions. After the keywords: Vos missions en quelques mots",
    )
    profile: Optional[str] = Field(
        default=None,
        description="Description of the seeked profile. After the keywords: Profil recherché",
    )
    application: Optional[str] = Field(
        default=None,
        description="Which document to provide for the application, who to contact to apply. After the keywords: Éléments de candidature",
    )
    employeur_description: Optional[str] = Field(
        default=None,
        description="Description of the employer. Can be after or before the keywords: Descriptif du service",
    )
    complementary_info: Optional[str] = Field(
        default=None,
        description="Additional informations, After the keywords: Informations complémentaires",
    )
    job_status: Optional[str] = Field(
        default=None,
        description="when the position will open, After the keywords: Statut du poste",
    )
    profession: Optional[str] = Field(
        default=None,
        description="Profession name of the job, After the keywords: Métier de référence",
    )


output_parser = PydanticOutputParser(pydantic_object=ExtractedContent)

# Ollama model setup.
ollama_llm = OllamaLLM(
    model="qwen2.5:3b",
    temperature=0,
    format="json",
    num_ctx=32768,
    num_predict=-2,  # -2 = fill context
    top_k=1,
    top_p=0.5,
)

# The prompt is in english despite the document being in french. English prompts showed slightly better performances
EXTRACT_INFO_FROM_JOBOFFER = """You are an expert extraction algorithm. 
You only extract the content that fits into the categories. 
Categories are given by the keywords that are the markdown headers.
IMPORTANT:
- No Paraphrasing: Use the exact words from the document. Do not rephrase or interpret the text.
- Headers (# ## ###) indicates topic boundaries
- Continue reading through the entire text even if you encounter irrelevant sentences
Some categories are long like 'missions' or 'profile'

Document:
{document}

{json_schema}
"""

EXTRACT_INFO_FROM_JOBOFFER_2 = """You are a precise document extraction system. Your task is to extract ALL content from each section delimited by markdown headers (# ## ###).

CRITICAL EXTRACTION RULES:
1. **Complete Section Extraction**: Extract EVERY sentence, paragraph, list item, and text fragment within each section until the next header
2. **Exact Text Preservation**: Use the original text verbatim - no paraphrasing, summarizing, or interpretation
3. **Section Boundaries**: A section starts after a markdown header (# ## ###) and ends when the next header begins
4. **Mixed Content Handling**: Sections may contain bullet points, numbered lists, paragraphs, and standalone sentences - capture ALL of them
5. **No Content Omission**: Do not skip content due to length, formatting, or apparent relevance

EXTRACTION PROCESS:
- Identify each markdown header as a section delimiter
- Extract ALL text content from that point until the next header
- Include both structured content (lists) and unstructured content (paragraphs)
- Maintain the logical flow but combine into the appropriate JSON field
- Ignore only: page markers like 'Afficher la suite'

SPECIAL ATTENTION:
- Long paragraphs that follow bullet points are still part of the same section
- Standalone sentences between sections belong to the preceding section
- Content that appears after lists but before the next header must be included

Document:
{document}

Required JSON Schema:
{json_schema}
"""

prompt_template = PromptTemplate(
    input_variables=["document"],
    template=EXTRACT_INFO_FROM_JOBOFFER_2,
    partial_variables={"json_schema": output_parser.get_format_instructions()},
)

# Create the chain
extraction_chain = prompt_template | ollama_llm


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

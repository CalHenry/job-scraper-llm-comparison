from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_ollama.llms import OllamaLLM

from src.ai_scrapper_jobmarket.models import ExtractedContent

output_parser = PydanticOutputParser(pydantic_object=ExtractedContent)


# Ollama model setup.
ollama_llm = OllamaLLM(
    model="qwen2.5:3b",
    temperature=0,
    format="json",
    num_ctx=32768,  # set the context window the 32K
    num_predict=-2,  # -2 = fill context
)

# The prompt is in english despite the document being in french. English prompts showed slightly better performances
EXTRACT_INFO_FROM_JOBOFFER = """You are a precise document extraction system. Your task is to extract ALL content from each section delimited by markdown headers (# ## ###).

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
    template=EXTRACT_INFO_FROM_JOBOFFER,
    partial_variables={"json_schema": output_parser.get_format_instructions()},
)

# Create the chain
extraction_chain = prompt_template | ollama_llm

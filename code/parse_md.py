from typing import Optional

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
        description="Reference of the page, number in 2 part with a year, a dash - and another number. After the keyword: Référence",
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
    profil: Optional[str] = Field(
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
    # model="qwen3:1.7b",
    model="qwen2.5:3b",
    temperature=0,
    format="json",
)

# The prompt is in english despite the document being in french. English prompt showed slightly better performances

EXTRACT_INFO_FROM_JOBOFFER = """You are an expert extraction algorithm. 
You only extract the content that fits into the categories. 
Almost all the categories are given by the keywords that are the markdown headers.
Almost all the document fits into a categorie.
IMPORTANT:
- Headers (# ## ###) indicates topic boundaries
- Continue reading through the entire text even if you encounter irrelevant sentences
- Look for content both before AND after any line breaks or interruptions
- ignore 'Afficher la suite'
The content 'title' is the first header (#)
Some categories are long like 'missions' or 'profil'
Document:
{document}

{json_schema}
"""

prompt_template = PromptTemplate(
    input_variables=["document"],
    template=EXTRACT_INFO_FROM_JOBOFFER,
    partial_variables={"json_schema": output_parser.get_format_instructions()},
)


def read_markdown_file(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def extract_content(document: str) -> dict:
    json_schema = (ExtractedContent.model_json_schema(),)
    raw_response = extraction_chain.invoke(input=document, json_schema=json_schema)
    job_data = ExtractedContent.model_validate_json(raw_response)
    return job_data


file_path = "outputs/results/tenta_3.md"

document = {"document": read_markdown_file(file_path)}


# Create the chain
extraction_chain = prompt_template | ollama_llm


extracted_content = extract_content(document)
print(f"{extracted_content.model_dump_json(indent=2)}")

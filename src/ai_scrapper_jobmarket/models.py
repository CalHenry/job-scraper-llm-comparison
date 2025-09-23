from typing import List, Optional

from pydantic import BaseModel, Field


# LLM pydantic model
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


# APEC API response pydantic models
class ApecJobOffer(BaseModel):
    "model for a single job offer"

    id: int
    intitule: str
    lieuTexte: str
    salaireTexte: Optional[str]
    texteOffre: str
    datePublication: Optional[str]
    typeContrat: Optional[str]
    contractDuration: Optional[int]
    url: str


class JobSearchResponse(BaseModel):
    "main model for the API response"

    resultats: List[ApecJobOffer] = Field(description="job offer content")
    totalCount: Optional[int] = Field(description="number of offers found")

from pathlib import Path
from typing import List, Tuple

import polars as pl
from polars import Expr
from polars._typing import IntoExpr
from polars.selectors import cs

"""
In this script we will process the markdown file of the job offer to have the right content in the right variable.
We will compare our result to the output of the LLM.

pros: 100% deterministic and instantaneous
cons: need go deeper into the document and do actual data manipulations. Weak to inconsistencies in the document headers

We use polars for string and data manipulation along with regex patterns
"""

# Import the markdown file as a single string
dir_path = "outputs/scrapping_results"
dir_path = Path(dir_path)
files_names = list(dir_path.glob("*.md"))
md_files = []
for file in files_names:
    with open(file) as f:
        content = f.read()
        md_files.append(content)


tenta_3_path = Path("outputs/scrapping_results/tenta_3.md")
with open(tenta_3_path) as f:
    tenta_3 = f.read()

# Pre-processing
"""
Steps:
"""

# In the terminal: I used 'rg '^\s*\*?\s*(?:##|###)'' in the dir with the .md files to output all the headers for all the files.
all_possible_headers = r"|".join(
    [
        r"Vos missions en quelques mots",  # always present
        r"Profil recherché",  # if not present look into 'missions'
        r"^Localisation",  # to remove
        r"Éléments de candidature",
        r"Documents à transmettre",  # only present if 'Éléments de candidature' exist
        r"Personnes à contacter",  # only present if 'Éléments de candidature' exist
        r"Descriptif du service",
        r"À propos de l'offre",  # always present
        r"Informations complémentaires",
        r"Conditions particulières d’exercice",
        r"Statut du poste",  # always present
        r"Métier de référence",  # always present
        r"Compétences attendues",  # concat with profile
        r"Niveau d'études minimum requis",  # concat with profile
        r"Langues",  # concat with profile
        r"Fondement juridique",  # concat with info
    ]
)


def clean_and_split(file):
    return (
        pl.Series("md_content", [file])
        .str.replace_all(pattern=r"(^|\s)###($|\s)", value="##")
        .str.replace_all(pattern=r"(^|\s)#($|\s)", value="##")
        .str.replace_all(r"\*+", "")
        .str.replace_all(r"Afficher la suite", "")
    ).str.split("## ")


# extract content with regex patterns
extract_content_from_col_0 = (
    (pl.col("column_0").str.extract(r"(.*)\sRéf.").alias("title")),
    (pl.col("column_0").str.extract(r"Référence :\s(.*)").alias("ref")),
    (pl.col("column_0").str.extract(r"Employeur :\s(.*)").alias("employeur_name")),
    (pl.col("column_0").str.extract(r"Localisation :\s(.*)").alias("loc")),
    (pl.col("column_0").str.extract(r"Expérience souhaitée\s(.*)").alias("experience")),
    (pl.col("column_0").str.extract(r"Catégorie\s(.*)").alias("cat")),
    (pl.col("column_0").str.extract(r"Télétravail possible\s(.*)").alias("remote")),
)


###### ######################################################################
def extract_or_column_name(series, pattern: str):
    extracted = series.str.extract_all(pattern=pattern).list.first().first()
    return extracted if extracted is not None else series.name


extract_test = [
    extract_or_column_name(s, all_possible_headers) for s in wip.iter_columns()
]

temp_df = (
    pl.DataFrame(clean_and_split(tenta_3)[0])
    .transpose()
    .with_columns(extract_content_from_col_0)
)

# Create the column mapping
column_mapping = dict(zip(temp_df.columns, extract_test))

# Apply the rename
wip = temp_df.rename(column_mapping)


###### ######################################################################


###### ######################################################################
def build_concat_expressions(
    configs: List[Tuple[str, List[str], str]], available_cols: List[str]
) -> List[IntoExpr]:
    """Build concatenation Polars expressions from config
    - IF the base col exist, we check if its related cols exist as well and create and expression to concat them if found
    - we refer to 'available_cols' to know which one is present or isn't
    - we use 'CONCAT_CONFIGS' to select the variable and set the alias for the concatenated column
    """
    expressions = []

    for base_col, potential_cols, alias in configs:
        if base_col in available_cols:
            existing_cols = [base_col] + [
                col for col in potential_cols if col in available_cols
            ]
            expr = pl.concat_str(
                [pl.col(col) for col in existing_cols], separator="\n"
            ).alias(alias)
            expressions.append(expr)

    return expressions


remove_noise_and_whitespaces = (
    pl.all()
    .str.strip_chars()
    .str.replace_all(
        r"^(.*?)\n", value=""
    )  # remove first line if it ends with a \n. To remove the headers artifacts
    # .str.replace_all(r"\n", value=" ") # replace newline by a blank
)

# Configuration:
CONCAT_CONFIGS: List[Tuple[str, List[str], str]] = [
    (
        "Éléments de candidature",  # base col
        ["Documents à transmettre", "Personnes à contacter"],  # [potential_cols]
        "application",  # alias
    ),
    (
        "Profil recherché",
        ["Compétences attendues", "Niveau d'études minimum requis", "Langues"],
        "profile",
    ),
    (
        "À propos de l'offre",
        [
            "Informations complémentaires",
            "Conditions particulières d'exercice",
            "Fondement juridique",
        ],
        "apropos",
    ),
]
FINAL_COLUMNS = [
    "title",
    "ref",
    "employeur_name",
    "loc",
    "experience",
    "cat",
    "remote",
    "missions",
    "profile",
    "application",
    "employeur_description",
    "complementary_info",
    "job_status",
    "profession",
]

# Build expressions
available_cols = set(wip.columns)
concat_expressions = build_concat_expressions(CONCAT_CONFIGS, available_cols)

# to see the expressiosn that will apply to the dataframe
[print(exp) for i, exp in enumerate(concat_expressions)]

# profile fallback
if "Profil recherché" not in available_cols:
    concat_expressions.append(
        pl.col("text").str.extract(r"(?i)(profil.*)", group_index=1).alias("profile")
    )

# Execute pipeline
wip_test_c = (
    wip.with_columns(concat_expressions)
    .rename(
        {
            "Vos missions en quelques mots": "missions",
            "Statut du poste": "job_status",
            "Métier de référence": "profession",
            **(
                {"Descriptif du service": "employeur_description"}
                if "Descriptif du service" in available_cols
                else {}
            ),
        }
    )
    .select(remove_noise_and_whitespaces)
    .select(cs.by_name(*FINAL_COLUMNS, require_all=False))
)
###### ######################################################################


def process_dataframe(
    cleanned_and_splitted: List[str],
    extract_content_from_col_1: Expr,
    COLUMN_MAPPING: dict,
    concat_columns: Expr,
    remove_noise_and_whitespaces: Expr,
    WANTED_ORDER: List,
) -> pl.DataFrame:
    """
    Process job offer content with string and data manipulations.
    Returns:
    - polars.DataFrame
    """
    return polars_parsing


def main():
    cleanned_and_splitted = [clean_and_split(file) for file in md_files]

    # Save as JSON for comparison with LLM output
    output_with_polars = Path("outputs/json_files/output_with_polars_2.json")
    combined_df.write_json(output_with_polars)


if __name__ == "__main__":
    main()

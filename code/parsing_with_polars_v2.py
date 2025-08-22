from pathlib import Path
from typing import List, Tuple

import polars as pl
import polars.selectors as cs
from polars._typing import IntoExpr

"""
In this script we process the markdown file of the job offer to filter the content and place the right parts in the right variable.
We will compare our result to the output of the LLM from the others script.

pros: 100% deterministic and instantaneous
cons: need go deeper into the document and do actual data manipulations. Weak to inconsistencies in the document content or structure

We use polars for string and dataframe manipulations along with regex patterns
"""

# Import the markdown files as a single string and place them into a List[str]
dir_path = "outputs/scrapping_results"
dir_path = Path(dir_path)
files_names = list(dir_path.glob("*.md"))
md_files = []
for file in files_names:
    with open(file) as f:
        content = f.read()
        md_files.append(content)


tenta_3_path = Path("outputs/scrapping_results/tenta_8.md")
with open(tenta_3_path) as f:
    tenta_3 = f.read()

"""
Steps:

1. Headers Extraction
   We use the command line with ripgrep to retrieve all headers from all markdown files.

2. Document Processing
   We clean and split the documents using the markdown headers as delimiters.

3. First Column Information Extraction
   We extract the information contained in the first column using simple regex patterns.

4. Dynamic Content Processing
   Since files don't have identical headers and some headers may be missing, our code has to be 
    dynamic to adapt to each file:

   Data Preparation:
   - Create a temporary dataframe with content extracted from the first column, placing it 
     into separate columns
   - Rename remaining columns based on a pre-configured mapping

   Polars Expression Processing:
   - Use Polars expressions to process the dataset (expressions concatenate and rename columns)
   - Generate expressions dynamically for each column present in the given file, allowing 
     adaptation to different file structures
   - Clean data by removing whitespaces and newline characters
   - Use a List[Tuple] to guide concatenation and naming of concatenated columns, handling 
     potential missing headers
   - Use a List[str] to keep and order only the desired columns in the final output

   DataFrame Processing Workflow:
   With these elements in place, we process the dataframe as follows:
   - Extract headers for the given file
   - Build expressions using the extracted headers
   - Implement a fallback mechanism in an if statement to extract profile information when 
     the column is missing (profile is key information)
   - Apply the expressions to the dataframe to:
     * Concatenate columns and rename them
     * Clean noise from the data
     * Select only the desired variables (if present)

5. Data Export
   Export the processed data as CSV and JSON formats (JSON allows comparison with LLM 
   processing of the same data).
"""

# Pre-processing:
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
        .str.replace_all(r"Afficher la suite", " ")
    ).str.split("##")


# extract content with regex patterns

extract_content_from_col_1 = (
    (pl.col("column_1").str.extract(r"(.*)\sRéf.").alias("title")),
    (pl.col("column_1").str.extract(r"Référence :\s(.*)").alias("ref")),
    (pl.col("column_1").str.extract(r"Employeur :\s(.*)").alias("employeur_name")),
    (pl.col("column_1").str.extract(r"Localisation :\s(.*)").alias("loc")),
    (pl.col("column_1").str.extract(r"Expérience souhaitée\s(.*)").alias("experience")),
    (pl.col("column_1").str.extract(r"Catégorie\s(.*)").alias("cat")),
    (pl.col("column_1").str.extract(r"Télétravail possible\s(.*)").alias("remote")),
)

###### ######################################################################


###### ######################################################################
def extract_or_column_name(series, pattern: str):
    extracted = series.str.extract_all(pattern=pattern).list.first().first()
    return extracted if extracted is not None else series.name


def process_md_to_dataframe(
    data,
    all_possible_headers=all_possible_headers,
    extract_content_from_col_1=extract_content_from_col_1,
    extract_or_column_name=extract_or_column_name,
):
    """
    Process a list of strings into DataFrames by transposing, extracting content, and renaming columns.
    """
    # Create temporary DataFrame
    temp_df = (
        pl.DataFrame(clean_and_split(data)[0])
        .transpose()
        .with_columns(extract_content_from_col_1)
    )

    # Extract column names
    extract_test = [
        extract_or_column_name(s, all_possible_headers) for s in temp_df.iter_columns()
    ]

    # Create the column mapping
    column_mapping = dict(zip(temp_df.columns, extract_test))

    return temp_df.rename(column_mapping)


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
    # .str.replace_all(r"\n", value=" ")
    # replace newline by a blank
)

# Configuration:
CONCAT_CONFIGS: List[Tuple[str, List[str], str]] = [
    (
        "Éléments de candidature",  # base col
        [
            "Documents à transmettre",
            "Personnes à contacter",
            "Descriptif du service",
        ],  # [potential_cols]
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


def clean_cols_with_expressions(
    wip,
    CONCAT_CONFIGS=CONCAT_CONFIGS,
    FINAL_COLUMNS=FINAL_COLUMNS,
    remove_noise_and_whitespaces=remove_noise_and_whitespaces,
):
    """
    Process a Polars DataFrame by building and applying concatenation expressions,
    renaming columns, and selecting final columns.
    """
    # Build expressions
    available_cols = set(wip.columns)
    concat_expressions = build_concat_expressions(CONCAT_CONFIGS, available_cols)

    # Print the expressions that will apply to the DataFrame
    # [print(exp) for i, exp in enumerate(concat_expressions)]

    # Profile fallback (add expression)
    if "Profil recherché" not in available_cols:
        for col_series in wip.iter_columns():  # look for the col that contain 'profile'
            has_profil = col_series.str.contains(r"(?i)profil").any()
            if has_profil:
                profil_column = col_series.name
                print(profil_column)

        concat_expressions.append(
            pl.col(f"{profil_column}")  # extract text from the col that has 'profile'
            .str.extract(
                r"(?i)(profil[^\n]*(?:\n[^\n]+)*)"
            )  # matches content after 'profil' until we encounter double new lines
            .alias("profile")
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

    return wip_test_c


###### ######################################################################


def main(json_output=True):
    cleanned_and_splitted = [process_md_to_dataframe(file) for file in md_files]

    final_df = [clean_cols_with_expressions(wip) for wip in cleanned_and_splitted]
    combined_df = pl.concat(final_df, how="diagonal")

    # Save as CSV for future usage
    output_csv = Path("outputs/csv_files/output_with_polars_2.csv")
    combined_df.write_csv(output_csv)

    if json_output:
        # Save as JSON for comparison with LLM output
        output_json = Path("outputs/json_files/output_with_polars_2.json")
        combined_df.write_json(output_json)


if __name__ == "__main__":
    main()

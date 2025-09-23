import argparse
import time
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


def parse_arguments():
    parser = argparse.ArgumentParser(description="Process markdown job offer files")
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="outputs/csv_files",
        help="Input path: either a directory containing .md files or a single .md file (default: outputs/test1)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="outputs/csv_files/polars_offer.csv",
        help="Output JSON file path (default: outputs/json_files/polars_offer_3.json)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Also save as JSON file (replaces .csv with .json in output path)",
    )
    return parser.parse_args()


# Import the markdown files as a single string and place them into a List[str]
def load_markdown_files(input_path: str) -> List[str]:
    """
    Load markdown files from either a single file or directory
    Returns a list of markdown content strings
    """
    input_path = Path(input_path)
    md_files = []
    is_single_file = False

    if input_path.is_file():
        # Single file processing
        if input_path.suffix.lower() != ".md":
            raise ValueError(f"File must be a .md file, got: {input_path}")

        with open(input_path) as f:
            content = f.read()
            md_files.append(content)
        is_single_file = True

    elif input_path.is_dir():
        # Directory processing
        files_names = list(input_path.glob("*.md"))

        if not files_names:
            raise ValueError(f"No .md files found in directory: {input_path}")

        for file in files_names:
            with open(file) as f:
                content = f.read()
                md_files.append(content)

    else:
        raise ValueError(f"Input path does not exist: {input_path}")

    return md_files, is_single_file


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
     adaptation to the different file structures
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


############################################################################


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
    )  # remove first line if it ends with a \n (it removes the headers artifacts)
    # .str.replace_all(r"\n", value=" ")
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

    # Print the expressions that will be applied to the DataFrame
    # [print(exp) for i, exp in enumerate(concat_expressions)]

    # Profile fallback (add expression)
    if "Profil recherché" not in available_cols:
        for col_series in wip.iter_columns():  # look for the col that contain 'profile'
            has_profil = col_series.str.contains(r"(?i)profil").any()
            if has_profil:
                profil_column = col_series.name
                offer_ref = wip.select("ref").item()
                print(
                    f"Found profile content in '{profil_column}' for offer '{offer_ref}'"
                )

        concat_expressions.append(
            pl.col(f"{profil_column}")  # extract text from the col that has 'profile'
            .str.extract(
                r"(?i)(profil[^\n]*(?:\n[^\n]+)*)"
            )  # matches content after 'profil' until we encounter double new lines
            .alias("profile")
        )

    # Execute pipeline
    final_df = (
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

    return final_df


############################################################################


def main():
    args = parse_arguments()

    md_files, is_single_file = load_markdown_files(args.input)

    # raw markdown --> temporary dataframes
    cleanned_and_splitted = [process_md_to_dataframe(file) for file in md_files]

    # temporary dataframes --> clean and organised dataframe
    final_df = [clean_cols_with_expressions(wip) for wip in cleanned_and_splitted]
    combined_df = pl.concat(final_df, how="diagonal")

    if is_single_file:
        # always output as JSON, file name will be
        input_path = Path(args.input)
        compare_results_dir = Path("outputs/compare_results")
        compare_results_dir.mkdir(parents=True, exist_ok=True)
        output_json = compare_results_dir / f"polars_{input_path.stem}.json"
        combined_df.write_json(output_json)

    else:
        # output path
        output_csv = Path(args.output)
        output_csv.parent.mkdir(
            parents=True, exist_ok=True
        )  # can create the dir if doesn't exist
        print(output_csv)
        # Save as CSV
        combined_df.write_csv(output_csv)

        # merge with existing csv file, removes duplicates
        if output_csv.exists():
            existing_df = pl.read_csv(output_csv)
            combined_df = pl.concat([existing_df, combined_df], how="diagonal").unique(
                subset="ref"
            )
        combined_df.write_csv(output_csv)

        # Save as JSON if requested
        if args.json:
            input_path = Path(args.input)
            # update the path for JSON files
            output_json_dir = output_csv.parent.parent / "json_file"
            output_json_dir.mkdir(parents=True, exist_ok=True)
            output_json = output_json_dir / f"{input_path.name}.json"
            combined_df.write_json(output_json)


if __name__ == "__main__":
    script_start = time.time()
    main()
    script_end = time.time()
    total_time = script_end - script_start
    print(f"Polars script execution time: {total_time:.2f}s")

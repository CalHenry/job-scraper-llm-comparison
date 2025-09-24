import argparse
from pathlib import Path
from typing import List, Tuple

import polars as pl
import polars.selectors as cs
from polars._typing import IntoExpr


def parse_arguments():
    parser = argparse.ArgumentParser(description="Process markdown job offer files")
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="data/processed/csv_files",
        help="Input path: either a directory containing .md files or a single .md file (default=data/processed/csv_files)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/processed/csv_files/polars_offer.csv",
        help="Output JSON file path (default=data/processed/csv_files/polars_offer.csv)",
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


def clean_and_split(file):
    return (
        pl.Series("md_content", [file])
        .str.replace_all(pattern=r"(^|\s)###($|\s)", value="##")
        .str.replace_all(pattern=r"(^|\s)#($|\s)", value="##")
        .str.replace_all(r"\*+", "")
        .str.replace_all(r"Afficher la suite", " ")
    ).str.split("##")


def extract_or_column_name(series, pattern: str):
    extracted = series.str.extract_all(pattern=pattern).list.first().first()
    return extracted if extracted is not None else series.name


def process_md_to_dataframe(
    data,
    all_possible_headers,
    extract_content_from_col_1,
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


def clean_cols_with_expressions(
    wip,
    CONCAT_CONFIGS,
    FINAL_COLUMNS,
    remove_noise_and_whitespaces,
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

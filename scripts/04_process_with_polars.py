import time
from pathlib import Path
from typing import List, Tuple

import polars as pl

from src.ai_scrapper_jobmarket.polars_processor import (
    clean_cols_with_expressions,
    load_markdown_files,
    parse_arguments,
    process_md_to_dataframe,
)

"""
In this script we process the markdown files of the job offers to filter the content and place the right parts in the right variable.
We will compare our result to the output of the LLM from the others script.

pros: 100% deterministic and instantaneous
cons: need go deeper into the document and do actual data manipulations. Weak to inconsistencies in the document content or structure

We use polars for string and dataframe manipulations along with regex patterns


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
# In the terminal: I used 'rg '^\s*\*?\s*(?:##|###)'' in the dir with the .md files to get all the headers for all the files.
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

############################################################################


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

############################################################################


def main():
    args = parse_arguments()

    md_files, is_single_file = load_markdown_files(args.input)

    # raw markdown --> temporary dataframes
    cleanned_and_splitted = [
        process_md_to_dataframe(file, all_possible_headers, extract_content_from_col_1)
        for file in md_files
    ]

    # temporary dataframes --> clean and organised dataframe
    final_df = [
        clean_cols_with_expressions(
            wip, CONCAT_CONFIGS, FINAL_COLUMNS, remove_noise_and_whitespaces
        )
        for wip in cleanned_and_splitted
    ]
    combined_df = pl.concat(final_df, how="diagonal")

    if is_single_file:
        # always output as JSON
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

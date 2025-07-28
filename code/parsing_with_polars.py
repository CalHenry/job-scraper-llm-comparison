from pathlib import Path

import polars as pl

"""
In this script we will process the markdown file of the job offer to have the right content in the right variable.
We will compare our result to the output of the LLM.

pros: 100% deterministic and instantaneous
cons: need go deeper into the document and do actual data manipulations. Weak to inconsistencies in the document headers
"""

# Import the markdown file as a single string
dir_path = "outputs/scrapping_results"
dir_path = Path(dir_path)
# files = list(dir_path.glob("*.md"))

tenta_3_path = Path("outputs/scrapping_results/tenta_3.md")
with open(tenta_3_path) as f:
    tenta_3 = f.read()


# Pre-processing
"""
We have to do a few pre-processing steps:
    - Convert the string to a polars object (Series)
    - Harmonised the headers (#, ##, ###) -> (##)
    - remove markdown synthax that is now noise (* or **)
    - remove irrelevant sentences identified while reading the output    
From there we split the series into a list of strings based on the headers.
"""

cleanned_and_splitted = (
    pl.Series([tenta_3])
    .str.replace_all(pattern=r"(^|\s)###($|\s)", value="##")
    .str.replace_all(pattern=r"(^|\s)#($|\s)", value="##")
    .str.replace_all(r"\*+", "")
    .str.replace_all(r"Afficher la suite", "")
).str.split("##")


# Cleanning and data processing
"""
Our intput is a List[str] (polars Series)
We will make several modifications to end up with a JSON file that has the same structured as the JSON from the LLM.
We will use Polars expressions to have a readable and clear code:
    - extract_content_from_col_1: 
    The first element of the list contains data for the firsts components, we extract them into new variables using str.extract() and REGEX patterns.
    - concat_columns: 
    After splitting based ont he headers in the preprocessing, the content of some component is speard on several columns.
    We use the handy str.concat_str() to merge the selected strings to one while creating a new variable.
    - clean_strings: 
    Since we imported the document as raw text, we have escape characters and white spaces that needs to be removed for a clean output.
    We use str.replace_all() with regex patterns.

With the expressions, we have isolated in the same object all the modifications that are alike.
With good naming of the expressions and the explicit polars's function names, we can have an immediate idea of what each expression do.

--> The block of code that actually modifies the data is 9 lines long (32 without the expressions).
--> Each line does a different modification to the dataframe.
--> Code structure designed for dual-level comprehension:
    - High-level overview for quick understanding
    - Granular organization to understand the actual code and logic while knowing where to look
"""
categories_order = [
    "title",
    "ref",
    "employeur_name",
    "loc",
    "experience",
    "cat",
    "remote",
    "missions",
    "profil",
    "application",
    "employeur_description",
    "complementary_info",
    "job_status",
    "profession",
]

col_names = {
    "column_2": "missions",
    "column_3": "profil",
    "column_5": "application",
    "column_8": "employeur_description",
    "column_10": "complementary_info",
    "column_12": "job_status",
    "column_13": "profession",
}

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

concat_columns = (
    pl.concat_str("application", "column_6", "column_7").alias("application"),
    pl.concat_str("employeur_description", "column_9").alias("employeur_description"),
    pl.concat_str("complementary_info", "column_11").alias("complementary_info"),
)

# remove noise and whitespaces
remove_noise_and_whitespaces = (
    pl.all()
    .str.strip_chars()
    .str.replace_all(r"^(.*?)\n", value="")
    .str.replace_all(r"\n", " ")
)

polars_parsing = (
    pl.DataFrame(cleanned_and_splitted[0], schema={"col1"})
    .transpose()  # from 1 var n rows to 1 row n vars
    .with_columns(extract_content_from_col_1)
    .rename(col_names)
    .with_columns(concat_columns)
    .drop(pl.col(r"^column_.*$"))  # drop variables called 'column_*'
    .select(remove_noise_and_whitespaces)
    .select(categories_order)  # reorder the cols
)

# Save as JSON for comparison with LLM output
output_with_polars = Path("outputs/parsing_results/output_with_polars.json")
polars_parsing.write_json("output_with_polars")

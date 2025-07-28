import polars as pl

# import json files

json_files_path = "outputs/parsing_results/"
df = pl.read_json(f"{json_files_path}tenta_3.json")


# df.write_csv(, separator=",")

tes = (
    pl.DataFrame(cleanned_and_splitted[0], schema={"col1"})
    .transpose()
    .with_columns(
        (pl.col("column_1").str.extract(r"(.*)\sRéf.").alias("title")),
        (pl.col("column_1").str.extract(r"Référence :\s(.*)").alias("ref")),
        (pl.col("column_1").str.extract(r"Employeur :\s(.*)").alias("employeur_name")),
        (pl.col("column_1").str.extract(r"Localisation :\s(.*)").alias("loc")),
        (
            pl.col("column_1")
            .str.extract(r"Expérience souhaitée\s(.*)")
            .alias("experience")
        ),
        (pl.col("column_1").str.extract(r"Catégorie\s(.*)").alias("cat")),
        (pl.col("column_1").str.extract(r"Télétravail possible\s(.*)").alias("remote")),
    )
    .rename(col_names)
    .with_columns(
        pl.concat_str("application", "column_6", "column_7").alias("application"),
        pl.concat_str("employeur_description", "column_9").alias(
            "employeur_description"
        ),
        pl.concat_str("complementary_info", "column_11").alias("complementary_info"),
    )
    .drop(pl.col(r"^column_.*$"))
    .select(
        pl.all()
        .str.strip_chars()
        .str.replace_all(r"^(.*?)\n", value="")
        .str.replace_all(r"\n", " ")
    )
    .select(categories_order)
)


tes.write_json("outputs/parsing_results/tes.json")

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


####
def apply_mapping(raw_data: dict, mapping_dic=code_mapping):
    # apply 'code_mapping' to change job type code to text
    transformed_data = copy.deepcopy(raw_data)

    def transform_recursive(data):
        if isinstance(raw_data, dict):
            for key, value in raw_data.items():
                if key == "typeContrat" and value in code_mapping:
                    raw_data[key] = code_mapping[value]
                elif isinstance(value, (dict, list)):
                    apply_mapping(value, code_mapping)
        elif isinstance(raw_data, list):
            for item in raw_data:
                apply_mapping(item, code_mapping)

    transform_recursive(transformed_data)
    return transformed_data


##############


# Build conditional expression
if "Éléments de candidature" in available_cols:
    concat_expr = (
        pl.when(
            # Case 1: Both additional columns exist - concat all three
            pl.lit("Documents à transmettre" in available_cols)
            & pl.lit("Personnes à contacter" in available_cols)
        )
        .then(
            pl.concat_str(
                [
                    "Éléments de candidature",
                    "Documents à transmettre",
                    "Personnes à contacter",
                ],
                separator="\n",
            )
        )
        .when(
            # Case 2: Only 'Documents à transmettre' exists
            pl.lit("Documents à transmettre" in available_cols)
        )
        .then(
            pl.concat_str(
                ["Éléments de candidature", "Documents à transmettre"], separator="\n"
            )
        )
        .when(
            # Case 3: Only 'Personnes à contacter' exists
            pl.lit("Personnes à contacter" in available_cols)
        )
        .then(
            pl.concat_str(
                ["Éléments de candidature", "Personnes à contacter"], separator="\n"
            )
        )
        .alias("cand")
    )

    wip_test = wip.with_columns(concat_expr)
else:
    print("no Éléments de candidature")

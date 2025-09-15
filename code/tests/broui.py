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


import json

with open("outputs/json_files/tenta_3.json", "r") as f:
    data = json.load(f)

text_field = data

print(repr(text_field))

print(text_field)

######


import polars as pl

dataset1 = pl.DataFrame(
    {
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "age": [25, 30, 35, 28, 32],
        "city": ["New York", "London", "Paris", "Tokyo", "Berlin"],
    }
)
dataset2 = pl.DataFrame(
    {
        "id": [3, 4, 6, 7, 8],
        "name": ["Charlie", "Diana", "Frank", "Grace", "Henry"],
        "age": [35, 28, 40, 26, 31],
        "city": ["Paris", "Tokyo", "Rome", "Madrid", "Sydney"],
    }
)

# Solution 1: Concat + unique (keeps first occurrence)
merged_df = pl.concat([dataset1, dataset2])
final_df = merged_df.unique()

print(final_df)


text = """# Une ou un data scientist
Réf. Référence :  2025-1863237 
* Fonction publique :  Fonction publique de l'État
* Employeur :  Cour des Comptes 
* Localisation :  13 rue Cambon 75001 Paris 
[ Domaine :  Numérique ](https://choisirleservicepublic.gouv.fr/metiers/numerique/)
  * [ TéléchargerPDF – 43.74Ko ](https://choisirleservicepublic.gouv.fr/wp-content/uploads/pdf-offers/pdf-2025-1863237/1747754432/une-ou-un-data-scientist-choisir-le-service-public.pdf)
  * Ajouter aux favoris : Une ou un data scientist


  * **Nature de l’emploi** Emploi ouvert aux titulaires et aux contractuels 
  * **Expérience souhaitée** Non renseigné 
  * **Rémunération** Fourchette indicative pour les contractuels Non renseignée  Fourchette indicative pour les fonctionnaires Non renseignée 
  * **Catégorie** Catégorie A (cadre) 
  * **Management** Non 
  * **Télétravail possible** Oui 


## Vos missions en quelques mots
Le département Analyse et Sciences des Données intervient notamment dans les domaines suivants :
- la collecte des données et l’analyse de la faisabilité des traitements ;
- le traitement des données (préparation, redressement, échantillonnage, scrapping…) ;
- l’analyse statistique (statistiques descriptives, économétrie, machine learning...) ;
- l’audit des données et des méthodologies quantitatives employées par l’administration ;
- la visualisation (infographies, cartographies, mise en place d’applications interactives Shiny...) ;
Afficher la suite
- l’ouverture des données ;
- l’animation autour de l’utilisation des données (communauté numérique, hackathons, ...).
Missions
Sous l’autorité de la cheffe de département analyse et science des données, la ou le data scientist aura pour mission d’apporter une expertise technique et méthodologique aux équipes de contrôle et de réaliser  
notamment les activités suivantes :
- Développer des requêtes, extraire des données, manipuler des données, pour faciliter leur exploitation par les équipes de contrôle des chambres thématiques ou juridictionnelles de la Cour à des fins d’analyse ;
- Réaliser des analyses statistiques et économétriques ;
- Renforcer sa connaissance du secteur public et notamment des finances publiques ;
- Utiliser des méthodes de data visualisation pour partager le résultat de ses analyses ;
- Développer des outils/applications pour les équipes de contrôle facilitant l’utilisation des données quantitatives et textuelles ;
- En cas d’appétence pour le sujet, proposer des cas d’usages de machine learning appliqués aux juridictions financières ;
- Apporter une expertise quantitative aux évaluations de politique publique effectuées par la Cour ou les chambres régionales et territoriales des comptes ;
- Assurer une veille et identifier les données pertinentes à acquérir et à traiter pour les travaux de la Cour des comptes ;
- Collaborer avec les organismes fournisseurs de données (INSEE, ministères,...) pour faciliter l’acquisition de ces données ;
- Assurer des animations autour de l’utilisation des données (organisation de hackathons, rassemblement de la communauté data de la Cour) ;
- Rendre compte de ses travaux sous forme d’annexes quantitatives et méthodologiques, pouvant être annexés aux rapports de la Cour.
- Possibilité de participer à des missions d’analyse des risques et d’audit de performances ou de terrain, voire d’audit financier, sur les entités et programmes qui relèvent de la responsabilité de la Cour dans le cadre de son mandat d’Audit Externe des Nations Unies (déplacements à prévoir).
## Profil recherché
Connaissances techniques :
- Maîtrise des méthodes d’analyse des données, de statistiques et d’économétrie
- Maîtrise des outils statistiques suivants : R et/ou python, SAS…
- Maîtrise de méthodes de programmation informatique (Python…)
- Maîtrise d’outils de requêtage, d’excel (VBA), de SAP Business Object, d’appariement de données…
- Compétences appréciées : Machine learning, R Shiny, PostgreSQL, web scraping, engagement dans une activité associative.
Afficher la suite
Autres compétences :
- Expérience sectorielle significative dans le domaine de santé ;
- Connaissance du secteur public
- Capacité à communiquer avec différents types d’acteurs de très haut niveau
- Très bonne communication écrite et orale
- Forte capacité d’écoute, force de conviction et diplomatie
- Autonomie, sens des responsabilités et implication
- Rigueur, esprit d’analyse et de synthèse
- Capacité à travailler en équipe
- Sens du service public
- Des connaissances dans le domaine des finances publiques et de la comptabilité publique seraient un plus appréciable.
## Localisation
Localisation : 13 Rue Cambon, 75001 Paris, France
  * Flèche gauche : déplacer la carte vers la gauche
  * Flèche droite : déplacer la carte vers la droite
  * Flèche bas : déplacer la carte vers le bas
  * Flèche haut : déplacer la carte vers le haut


C’est le fondement de notre mission : s’assurer du bon emploi de l’argent public et informer les citoyens. Juridiction financière indépendante créée en 1807, la Cour des comptes est aussi une institution moderne, ouverte sur l’extérieur, qui ne cesse d’évoluer et de se transformer dans une logique d’efficacité et d’exemplarité.
La Cour des comptes a quatre missions principales : elle contrôle tous les organismes et institutions recevant de l’argent public, juge les comptes des comptables publics, certifie les comptes de l’État et du régime général de sécurité sociale, et évalue les politiques publiques.
Afficher la suite
Chaque année, la Cour des comptes et ses sept chambres s’assurent de la bonne utilisation de l’argent public par les services de l’État, les établissements publics nationaux, les entreprises publiques, la sécurité sociale et par tout autre organisme en bénéficiant ou faisant appel à la générosité publique. Le contrôle est confié à un ou plusieurs « rapporteurs » assistés de « vérificateurs ».
Ces contrôles donnent lieu à des rapports qui peuvent être rendus publics. Ils consistent à apprécier de manière indépendante, objective et documentée, la régularité et la performance de la gestion d’une entité ou d’une activité. La Cour y présente les éventuels dysfonctionnements constatés et émet des recommandations pour en améliorer la gestion.
Par déclinaison, les Chambres Régionales et Territoriales des Comptes sont compétentes dans le jugement des comptes des comptables publics, le contrôle des comptes et de la gestion, le contrôle des actes budgétaires, et l’évaluation des politiques publiques mises en œuvre localement.
La Cour des comptes et les Chambres Régionales et Territoriales des Comptes constituent les Juridictions Financières.
### Descriptif du service
Elle est structurée en 7 départements permettant d’assurer la réalisation des missions qui lui sont confiées.
Au sein de la DNUM, le département Analyse et Sciences des Données, composé de 12 data-scientists, ainsi que de la cheffe de département et d’un adjoint, accompagne les équipes de contrôle notamment en offrant une expertise en matière de traitement analytique, statistique et graphique des données. Il contribue à l’acculturation numérique des JF par des actions de sensibilisation et de formation.
[ En savoir plus sur l'employeur ](https://choisirleservicepublic.gouv.fr/employeurs/cour-des-comptes/)
## À propos de l'offre
  * ###  Informations complémentaires
Le dossier de candidature devra comporter :
Ø une lettre de motivation adressée à M le Directeur des Ressources Humaines,
Ø un curriculum vitae,
Ø les trois derniers comptes-rendus d’entretiens professionnels,
Ø le dernier arrêté indiquant le grade et l’échelon,
Ø les copies des 3 dernières fiches de paye et, le cas échéant, des fiches de paye mentionnant tout élément indemnitaire non mensualisé (complément indemnitaire, bonus…) ou une fiche de rémunération annuelle fournie par l’administration d’origine (portant mention du traitement indiciaire et du détail des primes et indemnités qui seraient perçues au moment du recrutement).
Il sera adressé par courriel à l’adresse suivante : recrutement-datascientist@ccomptes.fr
Les candidates et candidats sélectionnés pourront être invités à se présenter à la chambre en vue d’un entretien.
RENSEIGNEMENTS COMPLEMENTAIRES
Tout renseignement complémentaire sur le poste peut être obtenu auprès de :
Lauriane Martzel, cheffe de département analyse et science des données
Tel : 01 72 63 52 26
e-mail : lauriane.martzel@ccomptes.fr
Les renseignements complémentaires sur la procédure recrutement peuvent être obtenus auprès de :
Hélène BUHANNIC, Chargée de recrutement
Mél : helene.buhannic@ccomptes.fr
Tel : 01 42 98 98 66
  * ###  Fondement juridique
Pour le (la) fonctionnaire d'Etat relevant du CIGeM (décret n° 2013-876 du 30 septembre 2013 et décret n° 2011-1317 du 17 octobre 2011), ou ingénieur SIC, l'intégration sera effective à la date d'accueil dans les juridictions financières.  
Le(La) fonctionnaire recruté(e) ne relevant pas du CIGeM sera placé(e) en position de détachement dans le corps des attachés d'administration de l'Etat ou ingénieur SIC pour une première période d'un an, renouvelable à l'issue.  
Les contractuels sont recrutés par la voie d'un contrat à durée déterminée de 3 ans.  
Sa rémunération sera prise en charge par la Cour des comptes. Le traitement indiciaire sera augmenté du montant du régime indemnitaire tenant compte des fonctions, des sujétions, de l'expertise et de l'engagement professionnel (RIFSEEP).
  * ###  Statut du poste
Susceptible d'être vacant à partir du 01/09/2025 
  * ###  Métier de référence
Data Scientist 
"""


def remove_punct_and_newlines(text):
    """
    Removes newlines from markdown content while preserving headers on their own lines.
    LLM are sensible to text structures and formating elements can be understood as end of content.
    Critical for LLMs to accurately process and interpret the content without missing context.
    """
    text = text.replace("-", "")
    text = text.replace("...", "")
    text = text.replace(".", "")
    text = text.replace(";", "")
    text = text.replace(":", "")
    text = text.replace("*", "")
    text = text.replace("Afficher la suite", "")
    text = text.replace("Missions", "")
    print(text)
    lines = text.strip().split("\n")
    result = []
    content_lines = []  # store non headers lines

    for line in lines:
        line = line.strip()
        if line.startswith("#"):
            # Join any accumulated content and add it
            if content_lines:
                result.append(" ".join(content_lines))
                content_lines = []
            # Add the header
            result.append(line)
        elif line:  # for any remaining lines
            content_lines.append(line)

    # Add any remaining content
    if content_lines:
        result.append(" ".join(content_lines))

    return "\n\n".join(result)


remove_punct_and_newlines(text)



#### command 
git diff --no-index --word-diff=color <(sed 's/\\n//g' compare_results/polars_offer_3.json) <(sed 's/\\n//g' compare_results/llm_offer_3.json)

git diff --no-index --word-diff=color <(sed 's/\\n//g' compare_results/polars_offer_3.json) <(sed 's/\\n//g' compare_results/llm_offer_3.json)

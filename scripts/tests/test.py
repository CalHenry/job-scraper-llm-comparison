import re
from pathlib import Path

import polars as pl

# Read the markdown file
file_path = Path("outputs/scrapping_results/tenta_10.md")
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

print("=== ORIGINAL CONTENT (first 500 chars) ===")
print(content[:500])
print("\n")

# Step 1: Clean and preprocess the content
cleaned_content = (
    pl.Series([content])
    .str.replace_all(r"(^|\n)###\s*", "\n## ")  # Convert ### to ##
    .str.replace_all(r"(^|\n)#\s*", "\n## ")  # Convert # to ##
    .str.replace_all(r"\*+", "")  # Remove markdown emphasis
    .str.replace_all(r"Afficher la suite", "")  # Remove "show more" text
    .str.replace_all(r"\s+", " ")  # Normalize whitespace
).item()

print("=== CLEANED CONTENT (first 500 chars) ===")
print(cleaned_content[:500])
print("\n")

# Step 2: Split content by ## headers
sections_raw = re.split(r"\n##\s*", cleaned_content, flags=re.IGNORECASE)
header_section = sections_raw[0]  # First part contains header info
content_sections = sections_raw[1:]  # Rest are the sections

print("=== HEADER SECTION ===")
print(header_section[:300])
print("\n")

print("=== CONTENT SECTIONS ===")
for i, section in enumerate(content_sections):
    section_header = section.split("\n")[0] if section else ""
    print(f"Section {i}: {section_header}")
print("\n")

# Step 3: Extract structured data from header section using regex
title_match = re.search(r"#\s*([^#\n]*?)(?:\s+Réf\.|$)", header_section, re.IGNORECASE)
ref_match = re.search(
    r"(?:Référence|Réf\.?)\s*:?\s*([^\n*]+)", header_section, re.IGNORECASE
)
employer_match = re.search(r"Employeur\s*:?\s*([^\n*]+)", header_section, re.IGNORECASE)
location_match = re.search(
    r"Localisation\s*:?\s*([^\n*]+)", header_section, re.IGNORECASE
)
experience_match = re.search(
    r"Expérience souhaitée\s*:?\s*([^\n*]+)", header_section, re.IGNORECASE
)
category_match = re.search(r"Catégorie\s*:?\s*([^\n*]+)", header_section, re.IGNORECASE)
remote_match = re.search(
    r"Télétravail possible\s*:?\s*([^\n*]+)", header_section, re.IGNORECASE
)

# Extract the matched values
title = title_match.group(1).strip() if title_match else ""
ref = ref_match.group(1).strip() if ref_match else ""
employeur_name = employer_match.group(1).strip() if employer_match else ""
loc = location_match.group(1).strip() if location_match else ""
experience = experience_match.group(1).strip() if experience_match else ""
cat = category_match.group(1).strip() if category_match else ""
remote = remote_match.group(1).strip() if remote_match else ""

print("=== EXTRACTED HEADER DATA ===")
print(f"Title: {title}")
print(f"Ref: {ref}")
print(f"Employer: {employeur_name}")
print(f"Location: {loc}")
print(f"Experience: {experience}")
print(f"Category: {cat}")
print(f"Remote: {remote}")
print("\n")

# Step 4: Map content sections to our fields using simple pattern matching
# Initialize all fields as empty
missions = ""
profil = ""
application = ""
employeur_description = ""
complementary_info = ""
job_status = ""
profession = ""

# Process each section
for section in content_sections:
    section_lines = section.split("\n", 1)
    section_header = section_lines[0].strip().lower()
    section_content = section_lines[1].strip() if len(section_lines) > 1 else ""

    print(f"Processing section: '{section_header[:50]}...'")

    # Clean the header for matching (remove punctuation)
    header_clean = re.sub(r"[^\w\s]", "", section_header)

    # Match patterns using simple contains logic
    missions_patterns = [
        "vos missions",
        "missions",
        "description du poste",
        "votre mission",
    ]
    profil_patterns = [
        "profil recherché",
        "profil",
        "votre profil",
        "compétences requises",
    ]
    application_patterns = [
        "éléments de candidature",
        "candidature",
        "comment postuler",
        "documents à transmettre",
    ]
    employer_patterns = ["à propos", "présentation", "lemployeur", "notre entreprise"]
    info_patterns = [
        "informations complémentaires",
        "conditions particulières",
        "informations diverses",
    ]
    status_patterns = ["statut du poste", "nature de lemploi", "type de contrat"]
    profession_patterns = ["métier de référence", "métier", "profession", "domaine"]

    # Check which pattern matches (using any() for cleaner logic)
    matched_field = ""
    if any(pattern in header_clean for pattern in missions_patterns):
        missions = missions + " " + section_content if missions else section_content
        matched_field = "missions"
    elif any(pattern in header_clean for pattern in profil_patterns):
        profil = profil + " " + section_content if profil else section_content
        matched_field = "profil"
    elif any(pattern in header_clean for pattern in application_patterns):
        application = (
            application + " " + section_content if application else section_content
        )
        matched_field = "application"
    elif any(pattern in header_clean for pattern in employer_patterns):
        employeur_description = (
            employeur_description + " " + section_content
            if employeur_description
            else section_content
        )
        matched_field = "employeur_description"
    elif any(pattern in header_clean for pattern in info_patterns):
        complementary_info = (
            complementary_info + " " + section_content
            if complementary_info
            else section_content
        )
        matched_field = "complementary_info"
    elif any(pattern in header_clean for pattern in status_patterns):
        job_status = (
            job_status + " " + section_content if job_status else section_content
        )
        matched_field = "job_status"
    elif any(pattern in header_clean for pattern in profession_patterns):
        profession = (
            profession + " " + section_content if profession else section_content
        )
        matched_field = "profession"

    print(f"  → Matched to: {matched_field}")

print("\n=== SECTION MATCHING RESULTS ===")
print(f"Missions length: {len(missions)}")
print(f"Profil length: {len(profil)}")
print(f"Application length: {len(application)}")
print(f"Employer description length: {len(employeur_description)}")
print(f"Complementary info length: {len(complementary_info)}")
print(f"Job status length: {len(job_status)}")
print(f"Profession length: {len(profession)}")
print("\n")

# Step 5: Clean all text fields using Polars
all_text_fields = [
    title,
    ref,
    employeur_name,
    loc,
    experience,
    cat,
    remote,
    missions,
    profil,
    application,
    employeur_description,
    complementary_info,
    job_status,
    profession,
]

cleaned_fields = (
    pl.Series(all_text_fields)
    .str.strip_chars()  # Remove leading/trailing whitespace
    .str.replace_all(r"\n+", " ")  # Replace newlines with spaces
    .str.replace_all(r"\s+", " ")  # Normalize multiple spaces
    .str.strip_chars()  # Final cleanup
).to_list()

print("=== FINAL CLEANED FIELDS ===")
field_names = [
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

for name, value in zip(field_names, cleaned_fields):
    print(f"{name}: {value[:100]}..." if len(value) > 100 else f"{name}: {value}")
print("\n")

# Step 6: Create the final DataFrame
final_data = {
    "title": cleaned_fields[0],
    "ref": cleaned_fields[1],
    "employeur_name": cleaned_fields[2],
    "loc": cleaned_fields[3],
    "experience": cleaned_fields[4],
    "cat": cleaned_fields[5],
    "remote": cleaned_fields[6],
    "missions": cleaned_fields[7],
    "profil": cleaned_fields[8],
    "application": cleaned_fields[9],
    "employeur_description": cleaned_fields[10],
    "complementary_info": cleaned_fields[11],
    "job_status": cleaned_fields[12],
    "profession": cleaned_fields[13],
}

result_df = pl.DataFrame([final_data])

print("=== FINAL DATAFRAME SHAPE ===")
print(f"Shape: {result_df.shape}")
print("\n")

# Step 7: Save as JSON
output_path = Path("outputs/json_files/simple_flexible_output.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
result_df.write_json(output_path)

print("=== PROCESSING COMPLETE ===")
print(f"Output saved to: {output_path}")
print("\nDataFrame preview:")
print(result_df.transpose(include_header=True))

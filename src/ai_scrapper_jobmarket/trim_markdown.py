def remove_with_keyword(markdown_text, keyword: str, lines_before=2):
    if keyword in markdown_text:
        all_lines = markdown_text.split("\n")

        # Find the line with the keyword
        for i, line in enumerate(all_lines):
            if keyword in line:
                # Calculate end position
                end_line = i - lines_before
                return "\n".join(all_lines[:end_line])

    return markdown_text

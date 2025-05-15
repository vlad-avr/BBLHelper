def tsv_to_markdown(tsv_str):
    lines = tsv_str.strip().split('\n')
    if not lines:
        return ""
    header = lines[0].split('\t')
    rows = [line.split('\t') for line in lines[1:]]
    md = "| " + " | ".join(header) + " |\n"
    md += "| " + " | ".join("---" for _ in header) + " |\n"
    for row in rows:
        md += "| " + " | ".join(row) + " |\n"
    return md
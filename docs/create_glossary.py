import pandas as pd
from pathlib import Path

xlsx = Path("glossary.xlsx")
out  = Path("Glossary.md")

sheets = pd.read_excel(xlsx, sheet_name=None)

lines = ["# Glossar", "",
         "_Automatisch generiert aus `glossary.xlsx`_", ""]

for seuche, df in sheets.items():
    lines.append(f"## {seuche}")
    lines.append("")
    lines.append(df.to_markdown(index=False))
    lines.append("")

out.write_text("\n".join(lines), encoding="utf-8")

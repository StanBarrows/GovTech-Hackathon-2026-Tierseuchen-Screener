from pathlib import Path
from rdflib import Graph

# Basisordner mit den TTL-Dateien
base_path = Path("lindas/RDFPoC/graphdb-poc/load")

# Ziel-Datei
output_file = base_path / "merged.ttl"

# Gemeinsamer RDF-Graph
g = Graph()

# Alle .ttl Dateien rekursiv laden
for ttl_file in base_path.rglob("*.ttl"):
    # merged.ttl selbst überspringen falls vorhanden
    if ttl_file.name == output_file.name:
        continue

    print(f"Lade: {ttl_file}")

    try:
        g.parse(ttl_file, format="turtle")
    except Exception as e:
        print(f"Fehler bei {ttl_file}: {e}")

# Zusammengeführten Graph speichern
g.serialize(destination=output_file, format="turtle")

print(f"\nFertig. Zusammengeführt nach: {output_file}")
print(f"Anzahl Triples: {len(g)}")

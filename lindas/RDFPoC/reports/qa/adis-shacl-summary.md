# ADIS SHACL Validation Summary

Status: **not executed** (dependency missing)

- SHACL engine `pyshacl` is not available in this environment.
- Per instruction, no dependency was installed automatically.

To run SHACL locally once approved:

```bash
python3 -m pip install pyshacl
pyshacl \
  -s ontology/adis-reference/v0.1.1/adis-reference-shapes-draft.ttl \
  -e ontology/adis-reference/v0.1.1/adis-reference-ontology.ttl \
  -d data/rdf/adis/adis-events.ttl \
  -d data/rdf/adis/adis-situations.ttl \
  -d data/rdf/adis/adis-skos-generated.ttl \
  -d data/rdf/adis/adis-source-rows.ttl \
  -f turtle \
  -o reports/qa/adis-shacl-report.ttl
```

Note: current shapes are draft structural checks and do not validate factual truth.

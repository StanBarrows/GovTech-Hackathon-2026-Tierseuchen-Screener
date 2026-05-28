# ADIS Outbreaks Schema

Source file: `data/structured/adis/adis-outbreaks-20260519.csv`

The source CSV contains 1,423 data rows and 46 columns. It is encoded with a UTF-8 BOM, uses semicolons as delimiters, double quotes for quoted fields, and comma decimal notation for coordinates.

ADIS is the EU Animal Disease Information System. The European Commission describes it as a system for registering, documenting, notifying, reporting, coordinating, and monitoring outbreaks of important infectious animal diseases in countries connected to the application. The official ADIS page also distinguishes primary outbreaks from secondary outbreaks and notes ADIS interoperability with WAHIS for international reporting context.

Official context: <https://food.ec.europa.eu/animals/animal-diseases/animal-disease-information-system-adis_en>

## Type Inference Notes

- `string`: free text or categorical text.
- `date`: ISO calendar date in `YYYY-MM-DD` format.
- `integer`: whole-number count or year.
- `decimal`: decimal number stored with a comma decimal separator in the CSV.
- `boolean`: literal `true` or `false`.
- Null values were inferred from blank-like markers: `NaN`, `N/A`, and empty values.

## Columns

| Column | Description | Inferred type | Nullable | Non-null | Null | Distinct | Example values |
|---|---|---|:---:|---:|---:|---:|---|
| `Reference` | ADIS outbreak identifier, combining country, disease/event code, year, and a generated suffix. | `string` | no | 1423 | 0 | 1423 | IT-SHB-2025-xghqg<br>DE-HPAI(NON-P)-2026-xsyaz<br>DE-HPAI(NON-P)-2026-yy25e |
| `National reference` | Reporting country's own outbreak or case reference number, where provided. | `string` | yes | 1127 | 296 | 1127 | SHB_2025_0016-zutgb<br>26-015-a0jke<br>26-015-mqw20 |
| `Country/Territory` | Country or territory that notified the outbreak. | `string` | no | 1423 | 0 | 31 | Italien<br>Deutschland<br>Island |
| `Typ` | Outbreak notification type; values indicate primary or secondary outbreak status. | `string` | no | 1423 | 0 | 2 | Secondary<br>Primary |
| `Disease name` | Reported disease or infection category for the outbreak. | `string` | no | 1423 | 0 | 19 | Aethina tumida (Inf. with)(Small hive beetle)(2006-)<br>HPAI(NON-P) in Wild Birds<br>Mycobacterium tuberculosis complex (Inf. with)(2019-) |
| `Disease type` | Disease subtype, strain, or serotype when reported separately from the disease name. | `string` | yes | 301 | 1122 | 4 | H5N1<br>H5N5<br>RABV |
| `Epidemiological unit` | Type of epidemiological unit affected, such as apiary, farm, forest, or body of water. | `string` | yes | 1319 | 104 | 9 | Apiary<br>Not applicable<br>Body of water |
| `Submitted on` | Date the outbreak notification was submitted to ADIS. | `date` | no | 1423 | 0 | 25 | 2026-05-13<br>2026-05-19<br>2026-04-20 |
| `Modified on` | Date the outbreak notification was last modified in ADIS. | `date` | no | 1423 | 0 | 25 | 2026-05-13<br>2026-05-19<br>2026-04-20 |
| `Administrative division level 1` | First-level administrative area for the outbreak location, such as region, state, or province. | `string` | no | 1423 | 0 | 170 | Sicily<br>Nordrhein-Westfalen<br>Hessen |
| `Administrative division level 2` | Second-level administrative area for the outbreak location, such as district or county. | `string` | yes | 1363 | 60 | 368 | Messina<br>Ennepe-Ruhr-Kreis<br>Hersfeld-Rotenburg |
| `Administrative division level 3` | Third-level administrative area for the outbreak location, often municipality or locality. | `string` | yes | 865 | 558 | 313 | Messina<br>Witten<br>Heringen (Werra) |
| `Outbreak occurring inside an already restricted zone` | Whether the outbreak occurred within a restriction zone already in place. | `boolean` | yes | 1346 | 77 | 2 | true<br>false |
| `Latitude` | Latitude of the reported outbreak location, using comma decimal notation in the CSV. | `decimal` | yes | 1319 | 104 | 1139 | 38,2093070701438<br>51,4100000000000<br>50,9100000000000 |
| `Longitude` | Longitude of the reported outbreak location, using comma decimal notation in the CSV. | `decimal` | yes | 1319 | 104 | 1155 | 15,521267481292263<br>7,350000000000000<br>10,010000000000000 |
| `Approximate location` | Whether the reported coordinates are approximate rather than exact. | `boolean` | yes | 1319 | 104 | 2 | false<br>true |
| `Location` | Human-readable place name associated with the outbreak coordinates or administrative area. | `string` | yes | 1319 | 104 | 511 | Messina<br>Witten<br>Heringen (Werra) |
| `Wildlife type 1` | Wildlife status of the affected animals when applicable. | `string` | yes | 1133 | 290 | 2 | Wild<br>Captive |
| `Production Type 1` | Production classification of affected birds or animals when applicable. | `string` | yes | 81 | 1342 | 2 | Poultry<br>Non-poultry birds |
| `Water type 1` | Water environment classification for aquatic outbreaks; empty in this extract. | `string` | yes | 0 | 1423 | 0 |  |
| `Production system 1` | Production system classification, populated only for a small number of aquatic or farming records. | `string` | yes | 1 | 1422 | 1 | Semi-closed (e.g. ponds or raceways) |
| `Measuring unit 1` | Unit used for population and outcome counts. | `string` | no | 1423 | 0 | 2 | Hives<br>Tiere |
| `Susceptible 1` | Count of susceptible animals, hives, or other measured units at the affected unit. | `integer` | yes | 288 | 1135 | 197 | 1<br>125<br>181 |
| `Cases 1` | Count of reported cases in the outbreak. | `integer` | yes | 1393 | 30 | 137 | 1<br>2<br>33 |
| `Dead 1` | Count of animals or units reported dead. | `integer` | yes | 1256 | 167 | 75 | 0<br>1<br>2 |
| `Killed 1` | Count of animals or units killed for disease control. | `integer` | yes | 730 | 693 | 118 | 0<br>1<br>2 |
| `Slaughtered 1` | Count of animals slaughtered in relation to the outbreak. | `integer` | yes | 501 | 922 | 4 | 0<br>2<br>1 |
| `Vaccinated 1` | Count of animals or units vaccinated in relation to the outbreak. | `integer` | yes | 351 | 1072 | 3 | 0<br>21<br>42 |
| `Outbreak year` | Calendar year assigned to the outbreak event. | `integer` | no | 1423 | 0 | 2 | 2025<br>2026 |
| `Suspicion/Start date` | Date of first suspicion or start of the outbreak event. | `date` | no | 1423 | 0 | 83 | 2025-12-10<br>2026-01-27<br>2026-01-19 |
| `Confirmation date` | Date the outbreak was confirmed. | `date` | no | 1423 | 0 | 57 | 2025-12-24<br>2026-01-30<br>2026-02-02 |
| `End date` | Date the outbreak was resolved or ended, where applicable. | `date` | yes | 784 | 639 | 56 | 2026-01-30<br>2026-04-17<br>2026-02-10 |
| `Status Continuing/Resolved` | Current outbreak status in the extract. | `string` | no | 1423 | 0 | 2 | Continuing<br>Resolved |
| `Suspicion` | Whether the record includes suspicion-only information; all non-null values are `false` in this extract. | `boolean` | no | 1423 | 0 | 1 | false |
| `Clinical signs` | Whether clinical signs were reported for the outbreak. | `boolean` | no | 1423 | 0 | 2 | true<br>false |
| `Diagnostic tests` | Whether diagnostic tests were reported for the outbreak. | `boolean` | no | 1423 | 0 | 2 | true<br>false |
| `Necropsy` | Whether necropsy findings were reported for the outbreak. | `boolean` | no | 1423 | 0 | 2 | false<br>true |
| `Category 1` | Broad diagnostic evidence category for the first reported test or observation. | `string` | yes | 1358 | 65 | 3 | Other (other than pathogen or antibody detection)<br>Pathogen detection<br>Antibody detection |
| `Subcategory 1` | More specific diagnostic evidence subcategory for the first reported test or observation. | `string` | yes | 1358 | 65 | 7 | Other (tests other than pathogen or antibody detection)<br>Nucleic acid detection<br>Antibody detection tests |
| `Test name 1` | Name of the first reported diagnostic test or identification method. | `string` | yes | 1358 | 65 | 18 | Morphological identification<br>Real-time polymerase chain reaction (real-time PCR)<br>Polymerase chain reaction (PCR) |
| `Test type 1` | Whether the first reported test was performed in a laboratory or in the field. | `string` | yes | 1358 | 65 | 2 | Laboratory<br>Field |
| `Laboratory type 1` | Type of laboratory that performed the first reported test. | `string` | yes | 1357 | 66 | 5 | National Reference Laboratory<br>Private Laboratory<br>Regional Reference Laboratory |
| `Species 1` | Affected species or taxonomic group for the first reported species entry. | `string` | yes | 1358 | 65 | 48 | Bees<br>Anser anser<br>Anserinae (unidentified) |
| `Result date 1` | Date of the first reported diagnostic result. | `date` | yes | 1358 | 65 | 56 | 2025-12-24<br>2026-01-30<br>2026-01-31 |
| `Result type 1` | Result of the first reported diagnostic test. | `string` | yes | 1358 | 65 | 2 | Positive<br>Negative |
| `Pertinence` | Reporting relevance category, indicating whether the outbreak is relevant to EU reporting only or both EU and WOAH reporting. | `string` | no | 1423 | 0 | 2 | EU and WOAH<br>EU |

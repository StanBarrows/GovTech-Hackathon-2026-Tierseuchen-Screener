# PAFF SHACL Quality Funnel (MVP)

This draft funnel validates **structure only**, not factual truth.

Why
- PAFF statements are unstructured/semi-structured narrative content.
- LLM/manual extraction produces candidate RDF only.
- SHACL ensures required links/fields exist before review, but does not certify epidemiological correctness.

Shapes used
- PaffReportShape
- OutbreakSituationShape
- OutbreakEventShape
- PaffSituationStatementShape
- EvidenceSnippetShape
- RelevanceAssessmentShape
- SeverityAssessmentShape
- ReachAssessmentShape
- ResearchReferenceShape

Funnel stages
1. Candidate extraction
   - Requires source report link, snippet evidence, extraction confidence/status
2. Situation linkage
   - Candidate statement must describe a ts:OutbreakSituation
3. Assessment linkage
   - Relevance/severity/reach assessments must assess situation and carry concept levels
4. Review readiness
   - Structural completeness supports human validation

Important
- SHACL pass ≠ true statement.
- Candidate data remains candidate until reviewed.
- Reach may be derived by rule and must carry rule reference when applicable.

We need to adapt the LiNDAS ontology in lindas/RDFPoC/ontology/adis-reference/v0.1.1/adis-reference-ontology.ttl for scraped news articles.

Current issue:
- ts:PaffReport and ts:PaffSituationStatement are PAFF-specific and must not be reused for Gefluegelnews or other scraped news.
- ts:Report is currently too thin and ADIS/reporting-system oriented; it only has submissionDate/modifiedDate and is linked from ts:OutbreakEvent via ts:hasReport.
- ts:SourceDocument is a good generic superclass for scraped documents.
- ts:OutbreakEvent is a good target when extracted news describes a concrete outbreak/event, but extraction output is candidate-level until reviewed.
- ts:ExtractionCandidate already exists but is not wired to source/evidence/status/assessments.

Please make a minimal backwards-compatible ontology extension:

1. Add class:
   ts:NewsReport a owl:Class ;
     rdfs:subClassOf ts:SourceDocument .

2. Add generic source-document properties:
   ts:sourcePublishedDate
     domain ts:SourceDocument ;
     range xsd:date .

   ts:sourceRetrievedAt
     domain ts:SourceDocument ;
     range xsd:dateTime .

   ts:sourcePublisher
     domain ts:SourceDocument ;
     range xsd:string .

   ts:sourceFullText
     domain ts:SourceDocument ;
     range xsd:string .
   Comment: cleaned Markdown/plain text representation, not raw HTML.

   ts:sourceContentHash
     domain ts:SourceDocument ;
     range xsd:string .

3. Generalize extraction candidate modelling:
   Add properties or widen existing domains so they apply to ts:ExtractionCandidate:
   - ts:extractedFromSource domain ts:ExtractionCandidate range ts:SourceDocument
   - ts:hasEvidenceSnippet domain ts:ExtractionCandidate range ts:EvidenceSnippet
   - ts:hasExtractionConfidence domain ts:ExtractionCandidate range skos:Concept
   - ts:hasExtractionStatus domain ts:ExtractionCandidate range skos:Concept
   - ts:hasRelevanceAssessment domain ts:ExtractionCandidate range ts:RelevanceAssessment
   - ts:hasSeverityAssessment domain ts:ExtractionCandidate range ts:SeverityAssessment
   - ts:hasReachAssessment domain ts:ExtractionCandidate range ts:ReachAssessment
   - ts:hasPreventionMeasure domain ts:ExtractionCandidate range ts:PreventionMeasure
   - ts:hasResearchReference domain ts:ExtractionCandidate range ts:ResearchReference

   Preserve existing PAFF triples/classes for backwards compatibility. Do not remove ts:PaffSituationStatement.

4. Link candidates to event/situation:
   Add:
   ts:candidateOutbreakEvent
     domain ts:ExtractionCandidate ;
     range ts:OutbreakEvent .

   ts:describesSituation should either have domain ts:ExtractionCandidate, or add:
   ts:candidateDescribesSituation
     domain ts:ExtractionCandidate ;
     range ts:OutbreakSituation .

5. Add generic evidence locator:
   ts:sourceTextLocator
     domain ts:EvidenceSnippet ;
     range xsd:string .
   Comment: paragraph index, character range, CSS selector, page/section locator, etc.

   Keep ts:sourceSlideNumber for PAFF/PDF use only.

6. Add consequence/impact modelling distinct from prevention:
   Add class:
   ts:Consequence a owl:Class .

   Add:
   ts:hasConsequence
     domain ts:ExtractionCandidate ;
     range ts:Consequence .

   ts:consequenceText
     domain ts:Consequence ;
     range xsd:string .

   ts:rawConsequenceEvidence
     domain ts:Consequence ;
     range xsd:string .

   Optional:
   ts:hasConsequenceType
     domain ts:Consequence ;
     range skos:Concept .

   This is needed because not all consequences are prevention measures. Examples: trade impact, economic loss, public-health implication, restriction zone, culling, monitoring, vaccination, farm closure.

7. Add SHACL shapes:
   - ts:NewsReportShape targeting ts:NewsReport:
     required ts:sourceDocumentTitle, ts:sourceURL, optional sourcePublishedDate, sourceRetrievedAt, sourceFullText, sourceContentHash.
   - ts:ExtractionCandidateShape targeting ts:ExtractionCandidate:
     required ts:extractedFromSource, ts:hasEvidenceSnippet, ts:hasExtractionStatus, ts:hasExtractionConfidence.
     optional candidateOutbreakEvent / candidateDescribesSituation.
   - Update EvidenceSnippetShape to allow ts:sourceTextLocator.

8. Add/update example Turtle for one Gefluegelnews article:
   - one ts:NewsReport with title, URL, published date, retrieved timestamp, full text/hash
   - one ts:ExtractionCandidate linked to the NewsReport
   - one or more ts:EvidenceSnippet with ts:sourceTextLocator
   - one candidate ts:OutbreakEvent when disease/country/month are available
   - one ts:OutbreakSituation using disease|country|YYYY-MM situation key
   - one ts:Consequence if the article mentions consequences
   - use existing SKOS confidence/status/relevance concepts.

Keep namespaces and existing files consistent with ontology version v0.1.1. Do not break the existing PAFF sample or ADIS RDF conversion.
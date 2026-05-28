<?php

namespace App\Services\Lindas\Mappers;

use App\Services\Lindas\Dto\SituationDetail;
use App\Services\Lindas\SparqlResults;

class SituationDetailMapper
{
    public function __construct(
        private readonly OutbreakEventMapper $eventMapper,
    ) {}

    public function map(SparqlResults $results): SituationDetail
    {
        $rows = $results->rows();
        $first = $rows[0] ?? [];

        $eventsByIri = [];

        foreach ($rows as $row) {
            $eventIri = $row['event'] ?? null;

            if (! is_string($eventIri) || $eventIri === '' || isset($eventsByIri[$eventIri])) {
                continue;
            }

            $eventsByIri[$eventIri] = $this->eventMapper->mapRow([
                'event' => $row['event'] ?? null,
                'eventRef' => $row['eventRef'] ?? null,
                'nationalRef' => $row['nationalRef'] ?? null,
                'confirmationDate' => $row['confirmationDate'] ?? null,
                'disease' => $row['disease'] ?? null,
                'subtype' => $row['subtype'] ?? null,
                'species' => $row['species'] ?? null,
                'admin1' => $row['admin1'] ?? null,
                'admin2' => $row['admin2'] ?? null,
                'admin3' => $row['admin3'] ?? null,
                'lat' => $row['lat'] ?? null,
                'lon' => $row['lon'] ?? null,
            ]);
        }

        return new SituationDetail(
            situationIri: (string) ($first['situation'] ?? ''),
            situationKey: isset($first['situationKey']) ? (string) $first['situationKey'] : null,
            situationMonth: isset($first['situationMonth']) ? (string) $first['situationMonth'] : null,
            situationDisease: isset($first['situationDisease']) ? (string) $first['situationDisease'] : null,
            situationCountry: isset($first['situationCountry']) ? (string) $first['situationCountry'] : null,
            statementIri: isset($first['stmt']) ? (string) $first['stmt'] : null,
            reportIri: isset($first['report']) ? (string) $first['report'] : null,
            snippetText: isset($first['snippetText']) ? (string) $first['snippetText'] : null,
            extractionStatus: isset($first['extractionStatus']) ? (string) $first['extractionStatus'] : null,
            extractionConfidence: isset($first['extractionConfidence']) ? (string) $first['extractionConfidence'] : null,
            relevanceLevel: isset($first['relevanceLevel']) ? (string) $first['relevanceLevel'] : null,
            severityLevel: isset($first['severityLevel']) ? (string) $first['severityLevel'] : null,
            reachLevel: isset($first['reachLevel']) ? (string) $first['reachLevel'] : null,
            preventionText: isset($first['preventionText']) ? (string) $first['preventionText'] : null,
            events: array_values($eventsByIri),
        );
    }
}

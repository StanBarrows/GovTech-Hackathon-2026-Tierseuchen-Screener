<?php

namespace App\Services\Lindas\Mappers;

use App\Services\Lindas\Dto\EntityCounts;
use App\Services\Lindas\SparqlResults;

class EntityCountsMapper
{
    public function map(SparqlResults $results): EntityCounts
    {
        $counts = [
            'OutbreakEvent' => 0,
            'OutbreakSituation' => 0,
            'PaffReport' => 0,
            'PaffSituationStatement' => 0,
            'EvidenceSnippet' => 0,
        ];

        foreach ($results->rows() as $row) {
            $type = $row['type'] ?? null;

            if (is_string($type) && array_key_exists($type, $counts)) {
                $counts[$type] = (int) ($row['count'] ?? 0);
            }
        }

        return new EntityCounts(
            outbreakEvents: $counts['OutbreakEvent'],
            outbreakSituations: $counts['OutbreakSituation'],
            paffReports: $counts['PaffReport'],
            paffSituationStatements: $counts['PaffSituationStatement'],
            evidenceSnippets: $counts['EvidenceSnippet'],
        );
    }
}

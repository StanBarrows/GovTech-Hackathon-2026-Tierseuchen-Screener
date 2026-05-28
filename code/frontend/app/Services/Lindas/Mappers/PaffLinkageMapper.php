<?php

namespace App\Services\Lindas\Mappers;

use App\Services\Lindas\Dto\PaffLinkage;
use App\Services\Lindas\SparqlResults;

class PaffLinkageMapper
{
    public function map(SparqlResults $results): ?PaffLinkage
    {
        $row = $results->first();

        if ($row === null) {
            return null;
        }

        return new PaffLinkage(
            eventIri: (string) ($row['event'] ?? ''),
            situationIri: isset($row['situation']) ? (string) $row['situation'] : null,
            statementIri: isset($row['stmt']) ? (string) $row['stmt'] : null,
            reportIri: isset($row['report']) ? (string) $row['report'] : null,
            snippetIri: isset($row['snippet']) ? (string) $row['snippet'] : null,
            relevance: isset($row['relevance']) ? (string) $row['relevance'] : null,
            relevanceLabel: null,
            severity: isset($row['severity']) ? (string) $row['severity'] : null,
            severityLabel: null,
            reach: isset($row['reach']) ? (string) $row['reach'] : null,
            reachLabel: null,
            prevention: isset($row['prevention']) ? (string) $row['prevention'] : null,
        );
    }
}

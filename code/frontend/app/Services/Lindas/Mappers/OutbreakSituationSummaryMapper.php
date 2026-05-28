<?php

namespace App\Services\Lindas\Mappers;

use App\Services\Lindas\Dto\OutbreakSituationSummary;
use App\Services\Lindas\SparqlResults;

class OutbreakSituationSummaryMapper
{
    /**
     * @return list<OutbreakSituationSummary>
     */
    public function mapMany(SparqlResults $results): array
    {
        return array_map(
            fn (array $row): OutbreakSituationSummary => $this->mapRow($row),
            $results->rows(),
        );
    }

    /**
     * @param  array<string, string|int|float|null>  $row
     */
    private function mapRow(array $row): OutbreakSituationSummary
    {
        return new OutbreakSituationSummary(
            iri: (string) ($row['situation'] ?? ''),
            key: isset($row['key']) ? (string) $row['key'] : null,
            disease: isset($row['disease']) ? (string) $row['disease'] : null,
            diseaseLabel: null,
            country: isset($row['country']) ? (string) $row['country'] : null,
            countryLabel: null,
            month: isset($row['month']) ? (string) $row['month'] : null,
            eventCount: (int) ($row['eventCount'] ?? 0),
        );
    }
}

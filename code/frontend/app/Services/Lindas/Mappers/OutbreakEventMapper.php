<?php

namespace App\Services\Lindas\Mappers;

use App\Services\Lindas\Dto\OutbreakEvent;
use App\Services\Lindas\SparqlResults;

class OutbreakEventMapper
{
    /**
     * @return list<OutbreakEvent>
     */
    public function mapMany(SparqlResults $results): array
    {
        return array_map(
            fn (array $row): OutbreakEvent => $this->mapRow($row),
            $results->rows(),
        );
    }

    /**
     * @param  array<string, string|int|float|null>  $row
     */
    public function mapRow(array $row): OutbreakEvent
    {
        return new OutbreakEvent(
            iri: (string) ($row['event'] ?? ''),
            referenceId: isset($row['eventRef']) ? (string) $row['eventRef'] : null,
            nationalReferenceId: isset($row['nationalRef']) ? (string) $row['nationalRef'] : null,
            confirmationDate: isset($row['confirmationDate']) ? (string) $row['confirmationDate'] : null,
            suspicionStartDate: isset($row['suspicionStartDate']) ? (string) $row['suspicionStartDate'] : null,
            situationIri: isset($row['situation']) ? (string) $row['situation'] : null,
            disease: isset($row['disease']) ? (string) $row['disease'] : null,
            diseaseLabel: isset($row['diseaseLabel']) ? (string) $row['diseaseLabel'] : null,
            subtype: isset($row['subtype']) ? (string) $row['subtype'] : null,
            subtypeLabel: isset($row['subtypeLabel']) ? (string) $row['subtypeLabel'] : null,
            species: isset($row['species']) ? (string) $row['species'] : null,
            speciesLabel: isset($row['speciesLabel']) ? (string) $row['speciesLabel'] : null,
            countryLabel: isset($row['countryLabel'])
                ? (string) $row['countryLabel']
                : (isset($row['country']) ? (string) $row['country'] : null),
            admin1: isset($row['admin1']) ? (string) $row['admin1'] : null,
            admin2: isset($row['admin2']) ? (string) $row['admin2'] : null,
            admin3: isset($row['admin3']) ? (string) $row['admin3'] : null,
            latitude: isset($row['lat']) ? (float) $row['lat'] : null,
            longitude: isset($row['lon']) ? (float) $row['lon'] : null,
        );
    }
}

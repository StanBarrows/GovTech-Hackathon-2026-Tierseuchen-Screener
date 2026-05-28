<?php

use App\Services\Lindas\Mappers\EntityCountsMapper;
use App\Services\Lindas\SparqlResults;

it('maps entity count rows into named totals', function () {
    $results = SparqlResults::fromArray([
        'head' => ['vars' => ['type', 'count']],
        'results' => [
            'bindings' => [
                [
                    'type' => ['type' => 'literal', 'value' => 'OutbreakEvent'],
                    'count' => ['type' => 'literal', 'value' => '1423', 'datatype' => 'http://www.w3.org/2001/XMLSchema#integer'],
                ],
                [
                    'type' => ['type' => 'literal', 'value' => 'PaffReport'],
                    'count' => ['type' => 'literal', 'value' => '1', 'datatype' => 'http://www.w3.org/2001/XMLSchema#integer'],
                ],
            ],
        ],
    ]);

    $dto = (new EntityCountsMapper)->map($results);

    expect($dto->outbreakEvents)->toBe(1423);
    expect($dto->paffReports)->toBe(1);
    expect($dto->toArray()['outbreakEvents'])->toBe(1423);
});

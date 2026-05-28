<?php

use App\Services\Lindas\Mappers\OutbreakEventMapper;
use App\Services\Lindas\Mappers\SituationDetailMapper;
use App\Services\Lindas\SparqlResults;

it('maps outbreak event rows with labels and coordinates', function () {
    $results = SparqlResults::fromArray([
        'head' => ['vars' => ['event', 'eventRef', 'lat', 'lon', 'diseaseLabel']],
        'results' => [
            'bindings' => [[
                'event' => ['type' => 'uri', 'value' => 'https://example.org/data/event-1'],
                'eventRef' => ['type' => 'literal', 'value' => 'DE-HPAI-1'],
                'lat' => ['type' => 'literal', 'value' => '48.12', 'datatype' => 'http://www.w3.org/2001/XMLSchema#decimal'],
                'lon' => ['type' => 'literal', 'value' => '11.57', 'datatype' => 'http://www.w3.org/2001/XMLSchema#decimal'],
                'diseaseLabel' => ['type' => 'literal', 'value' => 'HPAI(NON-P) in Wild Birds'],
            ]],
        ],
    ]);

    $event = (new OutbreakEventMapper)->mapMany($results)[0];

    expect($event->referenceId)->toBe('DE-HPAI-1');
    expect($event->latitude)->toBe(48.12);
    expect($event->toArray()['diseaseLabel'])->toBe('HPAI(NON-P) in Wild Birds');
});

it('aggregates situation detail rows by event iri', function () {
    $results = SparqlResults::fromArray([
        'head' => ['vars' => ['situation', 'situationKey', 'event', 'eventRef', 'stmt', 'report']],
        'results' => [
            'bindings' => [
                [
                    'situation' => ['type' => 'uri', 'value' => 'https://example.org/data/situation-1'],
                    'situationKey' => ['type' => 'literal', 'value' => 'hpai|de|2026-05'],
                    'event' => ['type' => 'uri', 'value' => 'https://example.org/data/event-1'],
                    'eventRef' => ['type' => 'literal', 'value' => 'DE-1'],
                    'stmt' => ['type' => 'uri', 'value' => 'https://example.org/data/stmt-1'],
                    'report' => ['type' => 'uri', 'value' => 'https://example.org/data/report-1'],
                ],
                [
                    'situation' => ['type' => 'uri', 'value' => 'https://example.org/data/situation-1'],
                    'situationKey' => ['type' => 'literal', 'value' => 'hpai|de|2026-05'],
                    'event' => ['type' => 'uri', 'value' => 'https://example.org/data/event-2'],
                    'eventRef' => ['type' => 'literal', 'value' => 'DE-2'],
                    'stmt' => ['type' => 'uri', 'value' => 'https://example.org/data/stmt-1'],
                    'report' => ['type' => 'uri', 'value' => 'https://example.org/data/report-1'],
                ],
            ],
        ],
    ]);

    $detail = (new SituationDetailMapper(new OutbreakEventMapper))->map($results);

    expect($detail->situationKey)->toBe('hpai|de|2026-05');
    expect($detail->events)->toHaveCount(2);
    expect($detail->toArray()['eventCount'])->toBe(2);
});

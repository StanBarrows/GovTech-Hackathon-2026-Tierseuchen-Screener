<?php

use App\Services\Lindas\LindasDataService;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;

beforeEach(function () {
    config(['services.lindas.cache_ttl' => 0]);
});

it('builds a validation snapshot from faked sparql responses', function () {
    Http::fake([
        'int.lindas.admin.ch/query*' => Http::sequence()
            ->push([
                'head' => ['vars' => ['type', 'count']],
                'results' => [
                    'bindings' => [[
                        'type' => ['type' => 'literal', 'value' => 'OutbreakEvent'],
                        'count' => ['type' => 'literal', 'value' => '2', 'datatype' => 'http://www.w3.org/2001/XMLSchema#integer'],
                    ]],
                ],
            ])
            ->push([
                'head' => ['vars' => ['event', 'eventRef', 'confirmationDate']],
                'results' => [
                    'bindings' => [[
                        'event' => ['type' => 'uri', 'value' => 'https://example.org/data/event-1'],
                        'eventRef' => ['type' => 'literal', 'value' => 'DE-1'],
                        'confirmationDate' => ['type' => 'literal', 'value' => '2026-05-04'],
                    ]],
                ],
            ]),
    ]);

    $snapshot = app(LindasDataService::class)->validationSnapshot('events', 1, 10);

    expect($snapshot['counts']['outbreakEvents'])->toBe(2);
    expect($snapshot['data'])->toHaveCount(1);
    expect($snapshot['data'][0]['referenceId'])->toBe('DE-1');
});

it('caches validation snapshots and avoids repeat sparql calls', function () {
    config(['services.lindas.cache_ttl' => 3600]);
    Cache::flush();

    Http::fake([
        'int.lindas.admin.ch/query*' => Http::sequence()
            ->push([
                'head' => ['vars' => ['type', 'count']],
                'results' => [
                    'bindings' => [[
                        'type' => ['type' => 'literal', 'value' => 'OutbreakEvent'],
                        'count' => ['type' => 'literal', 'value' => '1', 'datatype' => 'http://www.w3.org/2001/XMLSchema#integer'],
                    ]],
                ],
            ])
            ->push([
                'head' => ['vars' => ['event']],
                'results' => ['bindings' => []],
            ]),
    ]);

    $service = app(LindasDataService::class);

    $service->validationSnapshot('events', 1, 10);
    $service->validationSnapshot('events', 1, 10);

    Http::assertSentCount(2);
});

it('clears cached snapshots via cache bust', function () {
    config(['services.lindas.cache_ttl' => 3600]);
    Cache::flush();

    Http::fake([
        'int.lindas.admin.ch/query*' => Http::sequence()
            ->push([
                'head' => ['vars' => ['type', 'count']],
                'results' => [
                    'bindings' => [[
                        'type' => ['type' => 'literal', 'value' => 'OutbreakEvent'],
                        'count' => ['type' => 'literal', 'value' => '1', 'datatype' => 'http://www.w3.org/2001/XMLSchema#integer'],
                    ]],
                ],
            ])
            ->push([
                'head' => ['vars' => ['event']],
                'results' => ['bindings' => []],
            ])
            ->push([
                'head' => ['vars' => ['type', 'count']],
                'results' => [
                    'bindings' => [[
                        'type' => ['type' => 'literal', 'value' => 'OutbreakEvent'],
                        'count' => ['type' => 'literal', 'value' => '1', 'datatype' => 'http://www.w3.org/2001/XMLSchema#integer'],
                    ]],
                ],
            ])
            ->push([
                'head' => ['vars' => ['event']],
                'results' => ['bindings' => []],
            ]),
    ]);

    $service = app(LindasDataService::class);

    $service->validationSnapshot('events', 1, 10);
    $service->clearCache();
    $service->validationSnapshot('events', 1, 10);

    Http::assertSentCount(4);
});

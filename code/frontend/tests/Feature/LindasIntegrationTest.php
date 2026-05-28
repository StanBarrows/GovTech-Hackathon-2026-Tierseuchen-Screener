<?php

use App\Services\Lindas\LindasDataService;

it('fetches live entity counts from lindas int', function () {
    if (! filter_var(env('LINDAS_INTEGRATION', false), FILTER_VALIDATE_BOOL)) {
        $this->markTestSkipped('Set LINDAS_INTEGRATION=1 to run live LINDAS tests.');
    }

    $counts = app(LindasDataService::class)->entityCounts();

    expect($counts->outbreakEvents)->toBeGreaterThan(0);
})->group('integration');

it('fetches live outbreak events from lindas int', function () {
    if (! filter_var(env('LINDAS_INTEGRATION', false), FILTER_VALIDATE_BOOL)) {
        $this->markTestSkipped('Set LINDAS_INTEGRATION=1 to run live LINDAS tests.');
    }

    $events = app(LindasDataService::class)->outbreakEvents();

    expect($events)->not->toBeEmpty();
    expect($events[0]->iri)->not->toBe('');
})->group('integration');

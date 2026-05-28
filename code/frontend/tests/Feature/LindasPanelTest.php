<?php

use Illuminate\Support\Facades\Http;
use Inertia\Testing\AssertableInertia as Assert;

it('renders the lindas validation panel', function () {
    $this->withoutVite();
    config(['services.lindas.cache_ttl' => 0]);

    Http::fake([
        'int.lindas.admin.ch/query*' => Http::sequence()
            ->push([
                'head' => ['vars' => ['type', 'count']],
                'results' => ['bindings' => []],
            ])
            ->push([
                'head' => ['vars' => ['event']],
                'results' => ['bindings' => []],
            ]),
    ]);

    $response = $this->get(route('lindas'));

    $response->assertOk();
    $response->assertInertia(fn (Assert $page) => $page
        ->component('lindas')
        ->has('snapshot.counts')
        ->where('error', null));
});

it('shows an error banner when sparql fails', function () {
    $this->withoutVite();
    config(['services.lindas.cache_ttl' => 0]);

    Http::fake([
        'int.lindas.admin.ch/query*' => Http::response('upstream error', 500),
    ]);

    $response = $this->get(route('lindas'));

    $response->assertOk();
    $response->assertInertia(fn (Assert $page) => $page
        ->component('lindas')
        ->where('error', fn ($error) => is_string($error) && $error !== ''));
});

<?php

use App\Services\Lindas\LindasSparqlException;
use App\Services\Lindas\LindasSparqlService;
use App\Services\Lindas\SparqlResults;
use Illuminate\Support\Facades\Http;

it('parses sparql json bindings into rows', function () {
    $fixture = [
        'head' => ['vars' => ['type', 'count']],
        'results' => [
            'bindings' => [
                [
                    'type' => ['type' => 'literal', 'value' => 'OutbreakEvent'],
                    'count' => [
                        'type' => 'literal',
                        'value' => '1423',
                        'datatype' => 'http://www.w3.org/2001/XMLSchema#integer',
                    ],
                ],
            ],
        ],
    ];

    $results = SparqlResults::fromArray($fixture);

    expect($results->count())->toBe(1);
    expect($results->vars)->toBe(['type', 'count']);
    expect($results->first())->toBe([
        'type' => 'OutbreakEvent',
        'count' => 1423,
    ]);
});

it('sends sparql query to the configured lindas endpoint', function () {
    Http::fake([
        'int.lindas.admin.ch/query*' => Http::response([
            'head' => ['vars' => ['count']],
            'results' => [
                'bindings' => [
                    ['count' => ['type' => 'literal', 'value' => '1', 'datatype' => 'http://www.w3.org/2001/XMLSchema#integer']],
                ],
            ],
        ]),
    ]);

    $service = app(LindasSparqlService::class);
    $results = $service->select('SELECT (COUNT(?s) AS ?count) WHERE { ?s ?p ?o . }');

    expect($results->count())->toBe(1);

    Http::assertSent(function ($request) {
        return str_starts_with($request->url(), 'https://int.lindas.admin.ch/query')
            && ($request->data()['query'] ?? '') === 'SELECT (COUNT(?s) AS ?count) WHERE { ?s ?p ?o . }'
            && $request->hasHeader('Accept', 'application/sparql-results+json');
    });
});

it('wraps queries without a graph clause', function () {
    config(['services.lindas.graph_uri' => 'https://lindas.admin.ch/fsvo/govtech26-tierseuchen-screener']);

    $service = app(LindasSparqlService::class);

    $wrapped = $service->wrapInGraph(<<<'SPARQL'
PREFIX ts: <https://example.org/ontology#>
SELECT ?s WHERE {
  ?s a ts:Thing .
}
ORDER BY ?s
SPARQL);

    expect($wrapped)->toContain('GRAPH <https://lindas.admin.ch/fsvo/govtech26-tierseuchen-screener>');
    expect($wrapped)->toContain('} } ORDER BY');
});

it('throws when the endpoint returns an error status', function () {
    Http::fake([
        'int.lindas.admin.ch/query*' => Http::response('Service Unavailable', 503),
    ]);

    $service = app(LindasSparqlService::class);

    $service->select('SELECT * WHERE { ?s ?p ?o . } LIMIT 1');
})->throws(LindasSparqlException::class);

it('loads and sanitizes query files from the poc directory', function () {
    $service = app(LindasSparqlService::class);

    $query = $service->loadQueryFile('01-counts.rq');

    expect($query)->toContain('PREFIX ts:');
    expect($query)->toContain('GRAPH <https://lindas.admin.ch/fsvo/govtech26-tierseuchen-screener>');
    expect($query)->not->toContain('-----');
});

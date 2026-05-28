<?php

namespace App\Services\Lindas;

use Illuminate\Support\Facades\Http;

class LindasSparqlService
{
    public function select(string $sparql): SparqlResults
    {
        $endpoint = (string) config('services.lindas.sparql_endpoint');
        $timeout = (int) config('services.lindas.timeout');

        $response = Http::timeout($timeout)
            ->accept('application/sparql-results+json')
            ->get($endpoint, ['query' => trim($sparql)]);

        if (! $response->successful()) {
            throw new LindasSparqlException(
                "LINDAS SPARQL request failed (HTTP {$response->status()}): {$response->body()}",
            );
        }

        /** @var array<string, mixed> $data */
        $data = $response->json() ?? [];

        $this->assertNoSparqlError($data);

        return SparqlResults::fromArray($data);
    }

    public function queryFromFile(string $filename, bool $wrapGraph = false): SparqlResults
    {
        $sparql = $this->loadQueryFile($filename);

        if ($wrapGraph) {
            $sparql = $this->wrapInGraph($sparql);
        }

        return $this->select($sparql);
    }

    public function wrapInGraph(string $sparql): string
    {
        if (preg_match('/\bGRAPH\s*</i', $sparql)) {
            return $sparql;
        }

        $graphUri = (string) config('services.lindas.graph_uri');

        $sparql = preg_replace(
            '/WHERE\s*\{/i',
            "WHERE { GRAPH <{$graphUri}> {",
            $sparql,
            1,
        );

        if ($sparql === null) {
            throw new LindasSparqlException('Could not wrap SPARQL query in GRAPH clause.');
        }

        if (preg_match('/\}\s*(ORDER\s+BY|LIMIT|OFFSET|GROUP\s+BY)/i', $sparql)) {
            $sparql = preg_replace(
                '/\}\s*(ORDER\s+BY|LIMIT|OFFSET|GROUP\s+BY)/i',
                '} } $1',
                $sparql,
                1,
            );
        } else {
            $sparql = preg_replace('/\}\s*$/', '} }', $sparql, 1);
        }

        if ($sparql === null) {
            throw new LindasSparqlException('Could not close GRAPH clause in SPARQL query.');
        }

        return $sparql;
    }

    public function queriesBasePath(): string
    {
        $configured = config('services.lindas.queries_path');

        if (is_string($configured) && $configured !== '') {
            return rtrim($configured, '/');
        }

        return base_path('../../lindas/RDFPoC/graphdb-poc/queries');
    }

    public function loadQueryFile(string $filename): string
    {
        $basePath = realpath($this->queriesBasePath());

        if ($basePath === false) {
            throw new LindasSparqlException(
                'LINDAS queries directory not found: '.$this->queriesBasePath(),
            );
        }

        $basename = basename($filename);
        $fullPath = realpath($basePath.DIRECTORY_SEPARATOR.$basename);

        if ($fullPath === false || ! str_starts_with($fullPath, $basePath)) {
            throw new LindasSparqlException("LINDAS query file not found or not allowed: {$filename}");
        }

        $contents = file_get_contents($fullPath);

        if ($contents === false) {
            throw new LindasSparqlException("Could not read LINDAS query file: {$basename}");
        }

        return $this->sanitizeQuery($contents);
    }

    /**
     * @param  array<string, mixed>  $data
     */
    private function assertNoSparqlError(array $data): void
    {
        if (isset($data['error']) && is_string($data['error'])) {
            throw new LindasSparqlException('SPARQL error: '.$data['error']);
        }

        if (isset($data['message']) && is_string($data['message']) && ! isset($data['results'])) {
            throw new LindasSparqlException('SPARQL error: '.$data['message']);
        }
    }

    private function sanitizeQuery(string $contents): string
    {
        $lines = preg_split('/\r\n|\r|\n/', $contents) ?: [];
        $queryLines = [];
        $inBlockComment = false;

        foreach ($lines as $line) {
            $trimmed = trim($line);

            if (preg_match('/^-{3,}/', $trimmed)) {
                if (stripos($trimmed, 'Query2') !== false) {
                    break;
                }

                $inBlockComment = ! $inBlockComment;

                continue;
            }

            if ($inBlockComment) {
                continue;
            }

            if ($trimmed === '' && $queryLines === []) {
                continue;
            }

            $queryLines[] = $line;
        }

        return trim(implode("\n", $queryLines));
    }
}

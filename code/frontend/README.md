# Tierseuchen Screener — Frontend

Laravel 13 + Inertia + React 19 + Vite 8 + Tailwind 4, tested with Pest 4.

## Requirements

- PHP 8.3+ & Composer
- Node 20+ & npm

## Setup

```bash
composer setup
```

Runs `composer install`, copies `.env`, generates the app key, migrates the DB, installs npm deps, builds assets.

## Run locally

```bash
composer dev
```

Installs all required packages, herd starts the laravel server, Vite dev server..

Or run pieces individually:

```bash
php artisan serve   # http://localhost:8000
npm run dev         # Vite HMR
```

## Useful scripts

```bash
npm run build         # production build
npm run lint          # eslint --fix
npm run types:check   # tsc --noEmit
npm run format        # prettier
```

## LINDAS (read-only SPARQL)

The frontend can query outbreak and PAFF linkage data from the Swiss Federal Archives [LINDAS](https://lindas.admin.ch/) integration environment.

| Surface | URL |
|---------|-----|
| YASGUI (manual queries) | https://int.lindas.admin.ch/sparql/ |
| SPARQL API (used by the app) | https://int.lindas.admin.ch/query |
| Named graph | `https://lindas.admin.ch/fsvo/govtech26-tierseuchen-screener` |
| Dataset page | https://lindas.admin.ch/fsvo/fsvo-govtech26-tierseuchen-screener |

Read access is public (no credentials). Writes use GraphDB and are handled separately (see [lindas/lindas-endpoint.md](../../lindas/lindas-endpoint.md)).

### Configuration

Optional overrides in `.env`:

```env
# LINDAS_SPARQL_ENDPOINT=https://int.lindas.admin.ch/query
# LINDAS_GRAPH_URI=https://lindas.admin.ch/fsvo/govtech26-tierseuchen-screener
# LINDAS_SPARQL_TIMEOUT=30
# LINDAS_QUERIES_PATH=   # defaults to ../../lindas/RDFPoC/graphdb-poc/queries
```

### Smoke-test from the CLI

```bash
php artisan lindas:query --list
php artisan lindas:query counts
php artisan lindas:query situation-detail
```

Named queries load `.rq` files from `lindas/RDFPoC/graphdb-poc/queries/` (counts, situations, marker-paff, paff-events, situation-detail).

### Use in PHP

```php
use App\Services\Lindas\LindasQueryRepository;
use App\Services\Lindas\LindasSparqlService;

// Ad-hoc SPARQL
$results = app(LindasSparqlService::class)->select('SELECT (COUNT(?e) AS ?n) WHERE { ... }');
$rows = $results->rows();       // flattened bindings
$first = $results->first();     // first row or null

// Named PoC queries
$counts = app(LindasQueryRepository::class)->counts();
```

Queries without a `GRAPH` clause can be wrapped for LINDAS via `wrapInGraph()` (used for `LINDAS_Queries.rq`).

### Tests

```bash
php artisan test --filter=LindasSparql
LINDAS_INTEGRATION=1 php artisan test --filter=LindasIntegration
```

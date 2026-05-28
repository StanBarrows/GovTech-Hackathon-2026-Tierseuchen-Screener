<?php

namespace App\Console\Commands;

use App\Services\Lindas\Dto\OutbreakEventFilter;
use App\Services\Lindas\LindasDataService;
use App\Services\Lindas\LindasQueryRepository;
use App\Services\Lindas\LindasSparqlException;
use Illuminate\Console\Command;

class LindasQueryCommand extends Command
{
    /**
     * @var array<string, string>
     */
    private const QUERIES = [
        'counts' => 'Entity counts in the named graph',
        'events' => 'Paginated outbreak events',
        'situations' => 'Situations grouped with event counts',
        'marker-paff' => 'Single ADIS event linked to PAFF statement',
        'paff-events' => 'ADIS events for a PAFF report',
        'situation-detail' => 'Full situation + PAFF detail (demo IRIs)',
    ];

    protected $signature = 'lindas:query
                            {name? : Query name (counts, events, situations, marker-paff, paff-events, situation-detail)}
                            {--event= : OutbreakEvent IRI for marker-paff}
                            {--report= : PaffReport IRI for paff-events}
                            {--situation= : OutbreakSituation IRI for situation-detail}
                            {--stmt= : PaffSituationStatement IRI for situation-detail}
                            {--limit=50 : Page size for events}
                            {--page=1 : Page number for events}
                            {--list : List available query names}';

    protected $description = 'Run a named LINDAS SPARQL query against the integration endpoint';

    public function handle(LindasDataService $lindas): int
    {
        if ($this->option('list')) {
            $this->listQueries();

            return self::SUCCESS;
        }

        $name = $this->argument('name');

        if ($name === null) {
            $this->listQueries();
            $this->newLine();
            $this->error('Provide a query name or use --list.');

            return self::FAILURE;
        }

        if (! array_key_exists($name, self::QUERIES)) {
            $this->error("Unknown query name: {$name}");
            $this->listQueries();

            return self::FAILURE;
        }

        try {
            $payload = match ($name) {
                'counts' => $lindas->entityCounts()->toArray(),
                'events' => array_map(
                    fn ($event) => $event->toArray(),
                    $lindas->outbreakEvents(new OutbreakEventFilter(
                        limit: max(1, (int) $this->option('limit')),
                        offset: max(0, ((int) $this->option('page') - 1) * max(1, (int) $this->option('limit'))),
                    )),
                ),
                'situations' => array_map(
                    fn ($situation) => $situation->toArray(),
                    $lindas->situationsWithEventCounts(),
                ),
                'marker-paff' => $lindas->eventToPaffLinkage(
                    $this->option('event') ?: LindasQueryRepository::DEFAULT_EVENT_IRI,
                )?->toArray(),
                'paff-events' => array_map(
                    fn ($event) => $event->toArray(),
                    $lindas->paffReportToEvents(
                        $this->option('report') ?: LindasQueryRepository::DEFAULT_REPORT_IRI,
                    ),
                ),
                'situation-detail' => $lindas->situationDetail(
                    $this->option('situation') ?: LindasQueryRepository::DEFAULT_SITUATION_IRI,
                    $this->option('stmt') ?: LindasQueryRepository::DEFAULT_STMT_IRI,
                )->toArray(),
            };
        } catch (LindasSparqlException $e) {
            $this->error($e->getMessage());

            return self::FAILURE;
        }

        $this->info(self::QUERIES[$name]);
        $this->newLine();
        $this->line(json_encode($payload, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));

        return self::SUCCESS;
    }

    private function listQueries(): void
    {
        $this->info('Available LINDAS queries:');

        foreach (self::QUERIES as $name => $description) {
            $this->line("  <comment>{$name}</comment> — {$description}");
        }
    }
}

<?php

namespace App\Console\Commands;

use App\Services\Lindas\Dto\OutbreakEvent;
use App\Services\Lindas\Dto\OutbreakEventFilter;
use App\Services\Lindas\LindasDataService;
use App\Services\Lindas\LindasSparqlException;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\Storage;

class LindasSnapshotCommand extends Command
{
    public const SNAPSHOT_PATH = 'lindas-snapshot.json';

    private const FETCH_LIMIT = 1000000;

    protected $signature = 'lindas:snapshot
                            {--limit=1000000 : Max rows to fetch from LINDAS}
                            {--timeout=600 : HTTP timeout (seconds) for the SPARQL request}';

    protected $description = 'Fetch counts + all outbreak events from LINDAS once and write them to a JSON snapshot used by the dashboard.';

    public function handle(LindasDataService $lindas): int
    {
        set_time_limit(0);

        $limit = max(1, (int) $this->option('limit'));
        $timeout = max(30, (int) $this->option('timeout'));

        Config::set('services.lindas.timeout', $timeout);

        $this->line("Using SPARQL timeout: {$timeout}s");
        $this->info("Fetching entity counts from LINDAS…");

        try {
            $totals = $lindas->entityCounts()->toArray();
        } catch (LindasSparqlException $e) {
            $this->error('counts query failed: '.$e->getMessage());

            return self::FAILURE;
        }

        $this->line(sprintf('  outbreakEvents: %d', $totals['outbreakEvents'] ?? 0));

        $this->info("Fetching outbreak events (limit {$limit})…");

        try {
            $events = array_map(
                fn (OutbreakEvent $event): array => $event->toArray(),
                $lindas->outbreakEvents(new OutbreakEventFilter(limit: $limit)),
            );
        } catch (LindasSparqlException $e) {
            $this->error('events query failed: '.$e->getMessage());

            return self::FAILURE;
        }

        $this->line(sprintf('  rows: %d', count($events)));

        $payload = [
            'fetchedAt' => now()->toIso8601String(),
            'totals' => $totals,
            'events' => $events,
        ];

        $json = json_encode($payload, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);

        if ($json === false) {
            $this->error('Could not encode snapshot to JSON.');

            return self::FAILURE;
        }

        Storage::disk('local')->put(self::SNAPSHOT_PATH, $json);

        $this->info('Snapshot written: '.Storage::disk('local')->path(self::SNAPSHOT_PATH));

        return self::SUCCESS;
    }
}

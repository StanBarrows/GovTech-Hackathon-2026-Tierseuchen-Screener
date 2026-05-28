<?php

namespace App\Jobs;

use App\Console\Commands\LindasSnapshotCommand;
use App\Services\Lindas\Dto\OutbreakEvent;
use App\Services\Lindas\Dto\OutbreakEventFilter;
use App\Services\Lindas\LindasDataService;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;

class FetchLindasEventsChunk implements ShouldQueue
{
    use Dispatchable;
    use InteractsWithQueue;
    use Queueable;
    use SerializesModels;

    public const ACCUMULATOR_KEY = 'lindas:snapshot:events';

    public const STARTED_AT_KEY = 'lindas:snapshot:started-at';

    public const ACCUMULATOR_TTL = 3600 * 6;

    public int $timeout = 600;

    public int $tries = 3;

    public function __construct(
        public readonly int $offset = 0,
        public readonly int $chunkSize = 100,
    ) {}

    public function handle(LindasDataService $lindas): void
    {
        // Per-job HTTP timeout for slow LINDAS responses.
        Config::set('services.lindas.timeout', 300);

        Log::info('FetchLindasEventsChunk: fetching chunk', [
            'offset' => $this->offset,
            'chunkSize' => $this->chunkSize,
        ]);

        $events = $lindas->outbreakEvents(new OutbreakEventFilter(
            limit: $this->chunkSize,
            offset: $this->offset,
        ));

        $rows = array_map(
            fn (OutbreakEvent $event): array => $event->toArray(),
            $events,
        );

        $accumulator = Cache::get(self::ACCUMULATOR_KEY, []);

        if (! is_array($accumulator)) {
            $accumulator = [];
        }

        $accumulator = array_merge($accumulator, $rows);

        Cache::put(self::ACCUMULATOR_KEY, $accumulator, self::ACCUMULATOR_TTL);

        Log::info('FetchLindasEventsChunk: chunk merged', [
            'offset' => $this->offset,
            'rowsInChunk' => count($rows),
            'totalRows' => count($accumulator),
        ]);

        // Less than a full chunk → end of stream. Finalize snapshot.
        if (count($rows) < $this->chunkSize) {
            $this->finalize($lindas, $accumulator);

            return;
        }

        // Otherwise self-dispatch for the next chunk.
        self::dispatch($this->offset + $this->chunkSize, $this->chunkSize);
    }

    /**
     * @param  list<array<string, mixed>>  $rows
     */
    private function finalize(LindasDataService $lindas, array $rows): void
    {
        Log::info('FetchLindasEventsChunk: finalizing snapshot', [
            'totalRows' => count($rows),
        ]);

        $totals = $lindas->entityCounts()->toArray();

        $payload = [
            'fetchedAt' => now()->toIso8601String(),
            'startedAt' => Cache::get(self::STARTED_AT_KEY),
            'totals' => $totals,
            'events' => $rows,
        ];

        $json = json_encode($payload, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);

        if ($json === false) {
            Log::error('FetchLindasEventsChunk: JSON encode failed');

            return;
        }

        Storage::disk('local')->put(LindasSnapshotCommand::SNAPSHOT_PATH, $json);

        Cache::forget(self::ACCUMULATOR_KEY);
        Cache::forget(self::STARTED_AT_KEY);

        Log::info('FetchLindasEventsChunk: snapshot written', [
            'path' => Storage::disk('local')->path(LindasSnapshotCommand::SNAPSHOT_PATH),
            'totalRows' => count($rows),
            'totalsOutbreakEvents' => $totals['outbreakEvents'] ?? 0,
        ]);
    }
}

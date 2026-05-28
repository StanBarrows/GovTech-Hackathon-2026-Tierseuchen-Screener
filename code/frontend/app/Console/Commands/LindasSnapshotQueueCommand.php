<?php

namespace App\Console\Commands;

use App\Jobs\FetchLindasEventsChunk;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Cache;

class LindasSnapshotQueueCommand extends Command
{
    protected $signature = 'lindas:snapshot:queue
                            {--chunk=100 : Rows fetched per queued job}';

    protected $description = 'Kick off the chained LINDAS snapshot build by dispatching the first FetchLindasEventsChunk job.';

    public function handle(): int
    {
        $chunkSize = max(1, (int) $this->option('chunk'));

        Cache::forget(FetchLindasEventsChunk::ACCUMULATOR_KEY);
        Cache::put(
            FetchLindasEventsChunk::STARTED_AT_KEY,
            now()->toIso8601String(),
            FetchLindasEventsChunk::ACCUMULATOR_TTL,
        );

        FetchLindasEventsChunk::dispatch(0, $chunkSize);

        $this->info("Dispatched first chunk (size {$chunkSize}). Run `php artisan queue:work` to process the chain.");

        return self::SUCCESS;
    }
}

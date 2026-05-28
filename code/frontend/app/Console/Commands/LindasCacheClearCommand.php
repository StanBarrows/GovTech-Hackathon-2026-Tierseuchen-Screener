<?php

namespace App\Console\Commands;

use App\Services\Lindas\LindasDataService;
use Illuminate\Console\Command;

class LindasCacheClearCommand extends Command
{
    protected $signature = 'lindas:cache-clear';

    protected $description = 'Clear cached LINDAS SPARQL query results';

    public function handle(LindasDataService $lindas): int
    {
        $lindas->clearCache();

        $this->info('LINDAS cache cleared.');

        return self::SUCCESS;
    }
}

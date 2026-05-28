<?php

namespace App\Http\Controllers;

use App\Console\Commands\LindasSnapshotCommand;
use App\EventDto\EventDto;
use App\Services\Lindas\Dto\OutbreakEvent;
use Illuminate\Support\Facades\Storage;
use Inertia\Inertia;
use Inertia\Response;

class DashboardController extends Controller
{
    private const DEFAULT_CENTER_LAT = 46.9480;

    private const DEFAULT_CENTER_LNG = 7.4474;

    private const DEFAULT_RADIUS_KM = 50.0;

    public function map(): Response
    {
        $error = null;
        $events = [];
        $totals = [
            'outbreakEvents' => 0,
            'outbreakSituations' => 0,
            'paffReports' => 0,
            'paffSituationStatements' => 0,
            'evidenceSnippets' => 0,
        ];
        $fetchedAt = null;

        $snapshot = $this->readSnapshot();

        if ($snapshot === null) {
            $error = 'No LINDAS snapshot found. Run `php artisan lindas:snapshot` to generate one.';
        } else {
            $totals = array_merge($totals, $snapshot['totals'] ?? []);
            $fetchedAt = $snapshot['fetchedAt'] ?? null;

            $events = array_map(
                fn (array $row): array => EventDto::fromOutbreakEvent(OutbreakEvent::fromArray($row))
                    ->withRelevance(self::DEFAULT_CENTER_LAT, self::DEFAULT_CENTER_LNG, self::DEFAULT_RADIUS_KM)
                    ->toArray(),
                $snapshot['events'] ?? [],
            );
        }

        return Inertia::render('dashboard-map', [
            'cases' => $events,
            'error' => $error,
            'relevanceContext' => [
                'centerLat' => self::DEFAULT_CENTER_LAT,
                'centerLng' => self::DEFAULT_CENTER_LNG,
                'radiusKm' => self::DEFAULT_RADIUS_KM,
            ],
            'totals' => $totals,
            'snapshot' => [
                'fetchedAt' => $fetchedAt,
            ],
        ]);
    }

    /**
     * @return array{fetchedAt?: string, totals?: array<string, int>, events?: list<array<string, mixed>>}|null
     */
    private function readSnapshot(): ?array
    {
        $disk = Storage::disk('local');

        if (! $disk->exists(LindasSnapshotCommand::SNAPSHOT_PATH)) {
            return null;
        }

        $raw = $disk->get(LindasSnapshotCommand::SNAPSHOT_PATH);

        if ($raw === null) {
            return null;
        }

        $decoded = json_decode($raw, true);

        return is_array($decoded) ? $decoded : null;
    }
}

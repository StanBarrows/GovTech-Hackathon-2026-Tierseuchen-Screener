<?php

namespace App\Http\Controllers;

use App\Http\Resources\EventResource;
use App\Http\Resources\ReportResource;
use App\Models\Disease;
use App\Models\Event;
use App\Models\Report;
use App\Models\Species;
use App\Models\Subtype;
use App\Support\SeoMeta;
use Inertia\Inertia;
use Inertia\Response;

class DashboardController extends Controller
{
    private const DEFAULT_CENTER_LAT = 46.946461621956566;

    private const DEFAULT_CENTER_LNG = 7.4442526092578625;

    // Matches EventsSeeder::PROXIMITY_RADIUS_KM (the relevance decay scale) and the
    // frontend ORIGIN_RADIUS_KM, so the precomputed relevance_score is used directly.
    private const DEFAULT_RADIUS_KM = 120.0;

    public function map(): Response
    {
        return Inertia::render('dashboard-map', [
            'cases' => Inertia::defer(fn () => EventResource::collection(
                Event::query()->get(),
            )->resolve()),
            'reports' => Inertia::defer(fn () => ReportResource::collection(
                Report::query()->orderByDesc('report_date')->get(),
            )->resolve()),
            'error' => null,
            'relevanceContext' => [
                'centerLat' => self::DEFAULT_CENTER_LAT,
                'centerLng' => self::DEFAULT_CENTER_LNG,
                'radiusKm' => self::DEFAULT_RADIUS_KM,
            ],
            'diseaseOptions' => Disease::query()->orderBy('name')->pluck('name'),
            'speciesOptions' => Species::query()->orderBy('name')->pluck('name'),
            'subtypeOptions' => Subtype::query()->orderBy('name')->pluck('name'),
            'totals' => [
                'outbreakEvents' => Event::query()->count(),
                'outbreakSituations' => 0,
                'paffReports' => Report::query()->count(),
                'paffSituationStatements' => 0,
                'evidenceSnippets' => 0,
            ],
            'snapshot' => [
                'fetchedAt' => null,
            ],
            'seo' => SeoMeta::forPage([
                'title' => 'Karte',
                'description' => 'Interaktives Lagebild zu Tierseuchen-Ausbrüchen in der Schweiz.',
            ]),
        ]);
    }
}

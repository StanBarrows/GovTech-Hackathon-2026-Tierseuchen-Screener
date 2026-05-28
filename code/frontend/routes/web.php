<?php

use App\Http\Controllers\LindasController;
use Illuminate\Support\Facades\Route;
use Inertia\Inertia;

Route::redirect('/', '/dashboard/map')->name('home');

Route::get('/lindas', [LindasController::class, 'index'])->name('lindas');
Route::post('/lindas/cache/clear', [LindasController::class, 'clearCache'])->name('lindas.cache.clear');

Route::get('/imprint', fn () => Inertia::render('imprint'))->name('imprint');

Route::get('/dashboard/map', function () {
    // Deterministic synthetic HPAI events clustered around Swiss hotspots.
    mt_srand(42);

    $hotspots = [
        ['name' => 'Bern', 'lat' => 46.9480, 'lng' => 7.4474, 'spread' => 0.25, 'weight' => 18],
        ['name' => 'Zürich', 'lat' => 47.3769, 'lng' => 8.5417, 'spread' => 0.22, 'weight' => 16],
        ['name' => 'Bodensee', 'lat' => 47.6500, 'lng' => 9.2000, 'spread' => 0.30, 'weight' => 14],
        ['name' => 'Genfersee', 'lat' => 46.4500, 'lng' => 6.5500, 'spread' => 0.30, 'weight' => 12],
        ['name' => 'Sempachersee', 'lat' => 47.1450, 'lng' => 8.1700, 'spread' => 0.15, 'weight' => 8],
        ['name' => 'Neuenburgersee', 'lat' => 46.9300, 'lng' => 6.8500, 'spread' => 0.20, 'weight' => 8],
        ['name' => 'Thunersee', 'lat' => 46.6863, 'lng' => 7.7271, 'spread' => 0.18, 'weight' => 7],
        ['name' => 'St. Gallen', 'lat' => 47.4245, 'lng' => 9.3767, 'spread' => 0.18, 'weight' => 6],
        ['name' => 'Lugano', 'lat' => 46.0037, 'lng' => 8.9511, 'spread' => 0.20, 'weight' => 5],
        ['name' => 'Chur', 'lat' => 46.8499, 'lng' => 9.5320, 'spread' => 0.25, 'weight' => 4],
        ['name' => 'Basel', 'lat' => 47.5596, 'lng' => 7.5886, 'spread' => 0.18, 'weight' => 6],
    ];

    $totalWeight = array_sum(array_column($hotspots, 'weight'));
    $populations = ['wild', 'wild', 'wild', 'wild', 'wild', 'wild', 'wild', 'poultry', 'poultry', 'captive'];

    $speciesByPop = [
        'wild' => ['Graugans', 'Höckerschwan', 'Lachmöwe', 'Kormoran', 'Stockente', 'Reiherente'],
        'poultry' => ['Legehennen-Betrieb', 'Mastpoulet-Betrieb', 'Truthahn-Betrieb'],
        'captive' => ['Zoo-Vögel', 'Falknerei'],
    ];
    $subtypes = ['H5N1', 'H5N1', 'H5N1', 'H5N1', 'H5N1', 'H5N8', 'H5N5'];
    $sources = ['BLV', 'Kantonstierarzt', 'Labor', 'Tierarzt', 'Bürger-Meldung'];

    $populationWeights = [
        'poultry' => 5.0,
        'captive' => 2.0,
        'wild' => 1.0,
    ];
    $subtypeWeights = [
        'H5N1' => 1.5,
        'H5N8' => 1.2,
        'H5N5' => 1.0,
    ];
    $speciesWeights = [
        'Stockente' => 1.3,
        'Reiherente' => 1.3,
        'Graugans' => 1.3,
        'Höckerschwan' => 1.1,
        'Lachmöwe' => 1.1,
        'Kormoran' => 1.1,
    ];

    $cantonByName = [
        'Bern' => 'BE', 'Zürich' => 'ZH', 'Bodensee' => 'TG', 'Genfersee' => 'VD',
        'Sempachersee' => 'LU', 'Neuenburgersee' => 'NE', 'Thunersee' => 'BE',
        'St. Gallen' => 'SG', 'Lugano' => 'TI', 'Chur' => 'GR', 'Basel' => 'BS',
    ];

    $start = strtotime('2026-03-01 00:00');
    $end = strtotime('2026-05-28 23:59');
    $span = $end - $start;

    // Box-Muller for gaussian jitter.
    $gauss = function () {
        $u1 = (mt_rand(1, mt_getrandmax()) / mt_getrandmax());
        $u2 = (mt_rand(0, mt_getrandmax()) / mt_getrandmax());

        return sqrt(-2 * log($u1)) * cos(2 * M_PI * $u2);
    };

    $cases = [];
    for ($i = 1; $i <= 1000; $i++) {
        $roll = mt_rand(1, $totalWeight);
        $acc = 0;
        $hotspot = $hotspots[0];
        foreach ($hotspots as $h) {
            $acc += $h['weight'];
            if ($roll <= $acc) {
                $hotspot = $h;
                break;
            }
        }

        $pop = $populations[array_rand($populations)];
        $species = $speciesByPop[$pop][array_rand($speciesByPop[$pop])];
        $subtype = $subtypes[array_rand($subtypes)];

        $weight = round(
            ($populationWeights[$pop] ?? 1.0)
            * ($subtypeWeights[$subtype] ?? 1.0)
            * ($speciesWeights[$species] ?? 1.0),
            3,
        );

        $cases[] = [
            'id' => $i,
            'disease' => 'HPAI',
            'population' => $pop,
            'location' => $hotspot['name'],
            'canton' => $cantonByName[$hotspot['name']] ?? '',
            'species' => $species,
            'subtype' => $subtype,
            'weight' => $weight,
            'lat' => round($hotspot['lat'] + $gauss() * $hotspot['spread'], 4),
            'lng' => round($hotspot['lng'] + $gauss() * $hotspot['spread'], 4),
            'reportedAt' => date('Y-m-d\TH:i', $start + mt_rand(0, $span)),
            'source' => $sources[array_rand($sources)],
        ];
    }

    return Inertia::render('dashboard-map', ['cases' => $cases]);
})->name('dashboard.map');

<?php

namespace Database\Seeders;

use App\Enums\EventPriority;
use App\Models\Event;
use Illuminate\Database\Seeder;
use Illuminate\Support\Carbon;

class EventsSeeder extends Seeder
{
    /**
     * Number of synthetic HPAI events to generate.
     */
    private const COUNT = 10000;

    /**
     * Insert rows in chunks to keep SQLite happy and fast.
     */
    private const CHUNK = 500;

    /**
     * Operational origin ("Ausgangspunkt") — Bundesamt für Lebensmittelsicherheit
     * und Veterinärwesen, Bern. Distances and proximity scoring are relative to this.
     */
    private const BERN_LAT = 46.946461621956566;

    private const BERN_LNG = 7.4442526092578625;

    /**
     * Scoring tunables. relevance_score = W_PROXIMITY*proximity + W_DENSITY*density
     * + W_SEVERITY*severity, each term in [0, 1] → score in roughly [0, 5.2]. The
     * dashboard bins this into Hoch (>= 3) / Mittel (>= 1) / Tief, and the stored
     * priority enum uses the same thresholds.
     */
    private const PROXIMITY_RADIUS_KM = 120.0;   // proximity decay scale

    private const DENSITY_CELL_DEG = 0.1;        // ~11 km grid cell for the density histogram

    private const DENSITY_FULL = 150;            // neighbour count that saturates the density term

    private const SEVERITY_REF = 5000;           // case count that saturates the severity term

    private const W_PROXIMITY = 3.0;

    private const W_DENSITY = 1.5;

    private const W_SEVERITY = 0.7;

    /**
     * Seed ~10k HPAI (Geflügelpest) outbreak events forming a spatiotemporal
     * migration flow from northern Europe down to Switzerland over three months.
     *
     * Latitude is correlated with time: early March events sit in the north,
     * late May events arrive on the Swiss plateau — mimicking a bird flyway
     * carrying the virus southward.
     */
    public function run(): void
    {
        mt_srand(42);

        $disease = 'Geflügelpest (HPAI)';

        // Vögel (HPAI is avian) — German common names from ADIS data.
        $species = [
            'Habicht', 'Habichtartige', 'Nilgans', 'Stockente', 'Entenvögel', 'Graugans',
            'Kurzschnabelgans', 'Schneegans', 'Gänse', 'Steinadler', 'Vögel', 'Ringelgans',
            'Kanadagans', 'Weißwangengans', 'Uhu', 'Mäusebussard', 'Weißstorch', 'Störche',
            'Rohrweihe', 'Taubenvögel', 'Kolkrabe', 'Nebelkrähe', 'Saatkrähe', 'Dohle',
            'Schwäne', 'Singschwan', 'Höckerschwan', 'Wanderfalke', 'Falken', 'Silbermöwe',
            'Mittelmeermöwe', 'Rotmilan', 'Kormorane', 'Dreizehenmöwe',
        ];

        // Weighted pools (repetition encodes probability).
        $populations = array_merge(
            array_fill(0, 8, 'Wild'),
            array_fill(0, 2, 'Nutzgeflügel'),
            ['Gehaltene Vögel'],
        );
        $subtypes = ['H5N1', 'H5N1', 'H5N1', 'H5N1', 'H5N1', 'H5N5'];
        $sources = ['BLV', 'Kantonstierarzt', 'Labor', 'Tierarzt', 'Bürger-Meldung'];

        // Migration corridor: north (t=0, early) -> Switzerland (t=1, late).
        $corridor = [
            ['t' => 0.00, 'lat' => 55.30, 'lng' => 8.60, 'admin1' => 'Dänemark', 'admin2' => 'Syddanmark (Wattenmeer)'],
            ['t' => 0.12, 'lat' => 54.30, 'lng' => 9.00, 'admin1' => 'Schleswig-Holstein', 'admin2' => 'Nordfriesland'],
            ['t' => 0.25, 'lat' => 53.20, 'lng' => 9.00, 'admin1' => 'Niedersachsen', 'admin2' => 'Bremen/Hamburg'],
            ['t' => 0.40, 'lat' => 52.00, 'lng' => 9.30, 'admin1' => 'Nordrhein-Westfalen', 'admin2' => 'Ostwestfalen'],
            ['t' => 0.55, 'lat' => 50.50, 'lng' => 8.70, 'admin1' => 'Hessen', 'admin2' => 'Mittelhessen'],
            ['t' => 0.70, 'lat' => 49.00, 'lng' => 9.00, 'admin1' => 'Baden-Württemberg', 'admin2' => 'Heilbronn-Franken'],
            ['t' => 0.85, 'lat' => 47.70, 'lng' => 9.20, 'admin1' => 'Baden-Württemberg', 'admin2' => 'Bodensee'],
            ['t' => 1.00, 'lat' => 46.95, 'lng' => 7.60, 'admin1' => 'Schweiz', 'admin2' => 'Schweizer Mittelland'],
        ];

        // Swiss lake hotspots (lat <= ~47.7): cluster Swiss events on real cantons.
        $swissHotspots = [
            ['name' => 'Bern', 'lat' => 46.9480, 'lng' => 7.4474, 'spread' => 0.25, 'canton' => 'BE'],
            ['name' => 'Zürich', 'lat' => 47.3769, 'lng' => 8.5417, 'spread' => 0.22, 'canton' => 'ZH'],
            ['name' => 'Bodensee', 'lat' => 47.6500, 'lng' => 9.2000, 'spread' => 0.30, 'canton' => 'TG'],
            ['name' => 'Genfersee', 'lat' => 46.4500, 'lng' => 6.5500, 'spread' => 0.30, 'canton' => 'VD'],
            ['name' => 'Sempachersee', 'lat' => 47.1450, 'lng' => 8.1700, 'spread' => 0.15, 'canton' => 'LU'],
            ['name' => 'Neuenburgersee', 'lat' => 46.9300, 'lng' => 6.8500, 'spread' => 0.20, 'canton' => 'NE'],
            ['name' => 'Thunersee', 'lat' => 46.6863, 'lng' => 7.7271, 'spread' => 0.18, 'canton' => 'BE'],
            ['name' => 'St. Gallen', 'lat' => 47.4245, 'lng' => 9.3767, 'spread' => 0.18, 'canton' => 'SG'],
            ['name' => 'Chur', 'lat' => 46.8499, 'lng' => 9.5320, 'spread' => 0.25, 'canton' => 'GR'],
            ['name' => 'Basel', 'lat' => 47.5596, 'lng' => 7.5886, 'spread' => 0.18, 'canton' => 'BS'],
        ];

        $start = Carbon::parse('2026-03-01 00:00');
        $end = Carbon::parse('2026-05-28 23:59');
        $span = $end->getTimestamp() - $start->getTimestamp();

        $now = Carbon::now()->format('Y-m-d H:i:s');

        // Pass 1 — generate rows and tally a coarse density histogram keyed by grid cell.
        $rows = [];
        $histogram = [];

        for ($i = 1; $i <= self::COUNT; $i++) {
            // Skew slightly toward Switzerland so density builds up in the south.
            $t = (mt_rand(0, mt_getrandmax()) / mt_getrandmax()) ** 0.7;

            // Time follows the corridor parameter, with a few days of jitter.
            $offset = (int) round($t * $span + $this->gauss() * 3 * 86400);
            $occurredTs = max(0, min($span, $offset));
            $occurredAt = $start->copy()->addSeconds($occurredTs)->format('Y-m-d H:i:s');

            [$lat, $lng] = $this->interpolate($corridor, $t);
            $lat += $this->gauss() * 0.35;
            $lng += $this->gauss() * 0.50;

            $population = $populations[array_rand($populations)];

            if ($lat <= 47.7) {
                // Swiss band: snap onto a lake hotspot for realistic clustering.
                $hotspot = $swissHotspots[array_rand($swissHotspots)];
                $lat = $hotspot['lat'] + $this->gauss() * $hotspot['spread'];
                $lng = $hotspot['lng'] + $this->gauss() * $hotspot['spread'];
                $admin1 = $hotspot['canton'];
                $admin2 = $hotspot['name'];
            } else {
                $waypoint = $this->nearestWaypoint($corridor, $t);
                $admin1 = $waypoint['admin1'];
                $admin2 = $waypoint['admin2'];
            }

            [$cases, $deaths, $susceptible] = $this->outbreakCounts($population);

            $cellRow = (int) round($lat / self::DENSITY_CELL_DEG);
            $cellCol = (int) round($lng / self::DENSITY_CELL_DEG);
            $cellKey = $cellRow.':'.$cellCol;
            $histogram[$cellKey] = ($histogram[$cellKey] ?? 0) + 1;

            $rows[] = [
                'disease' => $disease,
                'subtype' => $subtypes[array_rand($subtypes)],
                'species' => $species[array_rand($species)],
                'population' => $population,
                'source' => $sources[array_rand($sources)],
                'external_id' => 'HPAI-2026-'.str_pad((string) $i, 6, '0', STR_PAD_LEFT),
                'occurred_at' => $occurredAt,
                'admin_level_1' => $admin1,
                'admin_level_2' => $admin2,
                'admin_level_3' => null,
                'latitude' => round($lat, 6),
                'longitude' => round($lng, 6),
                'cases' => $cases,
                'deaths' => $deaths,
                'susceptible' => $susceptible,
                'distance_km' => null,
                'relevance_score' => null,
                'priority' => null,
                'created_at' => $now,
                'updated_at' => $now,
                '_cellRow' => $cellRow,
                '_cellCol' => $cellCol,
            ];
        }

        // Pass 2 — score each row (distance to Bern, density, severity) and bin priority.
        $buffer = [];

        foreach ($rows as $row) {
            $distance = $this->haversineKm(
                (float) $row['latitude'],
                (float) $row['longitude'],
                self::BERN_LAT,
                self::BERN_LNG,
            );

            $proximity = exp(-$distance / self::PROXIMITY_RADIUS_KM);

            // Sum the row's own cell plus the 8 surrounding cells ≈ a radial neighbour count.
            $neighbours = 0;
            for ($dr = -1; $dr <= 1; $dr++) {
                for ($dc = -1; $dc <= 1; $dc++) {
                    $neighbours += $histogram[($row['_cellRow'] + $dr).':'.($row['_cellCol'] + $dc)] ?? 0;
                }
            }
            $density = min(1.0, $neighbours / self::DENSITY_FULL);

            // Log-scaled so a handful of dead wild birds and a large farm outbreak
            // don't collapse to the extremes.
            $severity = min(1.0, log10($row['cases'] + 1) / log10(self::SEVERITY_REF));

            $score = self::W_PROXIMITY * $proximity
                + self::W_DENSITY * $density
                + self::W_SEVERITY * $severity;

            $priority = match (true) {
                $score >= 3.0 => EventPriority::High,
                $score >= 1.0 => EventPriority::Medium,
                default => EventPriority::Low,
            };

            unset($row['_cellRow'], $row['_cellCol']);
            $row['distance_km'] = round($distance, 2);
            $row['relevance_score'] = round($score, 2);
            $row['priority'] = $priority->value;

            $buffer[] = $row;

            if (count($buffer) >= self::CHUNK) {
                Event::query()->insert($buffer);
                $buffer = [];
            }
        }

        if ($buffer !== []) {
            Event::query()->insert($buffer);
        }
    }

    /**
     * Generate realistic case / death / susceptible counts for a population, keeping
     * the invariant deaths <= cases <= susceptible.
     *
     * @return array{0: int, 1: int, 2: int}
     */
    private function outbreakCounts(string $population): array
    {
        switch ($population) {
            case 'Nutzgeflügel':
                // Commercial poultry flock; a fraction of the flock falls ill.
                $susceptible = mt_rand(200, 12000);
                $cases = max(1, (int) round($susceptible * (mt_rand(2, 15) / 100)));
                $deaths = mt_rand((int) round($cases * 0.3), $cases);
                break;

            case 'Gehaltene Vögel':
                // Captive / backyard holding; small numbers.
                $susceptible = mt_rand(3, 150);
                $cases = max(1, (int) round($susceptible * (mt_rand(5, 40) / 100)));
                $deaths = mt_rand(0, $cases);
                break;

            default:
                // Wild birds, usually found dead in small numbers (high mortality).
                $susceptible = mt_rand(1, 20);
                $cases = mt_rand(1, $susceptible);
                $deaths = mt_rand((int) ceil($cases * 0.6), $cases);
                break;
        }

        return [$cases, $deaths, $susceptible];
    }

    /**
     * Great-circle distance in kilometres between two lat/lng points (Haversine).
     * Mirrors the frontend helper in resources/js/lib/case-relevance.ts.
     */
    private function haversineKm(float $lat, float $lng, float $bLat, float $bLng): float
    {
        $earthKm = 6371.0;
        $dLat = deg2rad($bLat - $lat);
        $dLng = deg2rad($bLng - $lng);

        $h = sin($dLat / 2) ** 2
            + cos(deg2rad($lat)) * cos(deg2rad($bLat)) * sin($dLng / 2) ** 2;

        return 2 * $earthKm * asin(min(1.0, sqrt($h)));
    }

    /**
     * Linearly interpolate the corridor lat/lng at parameter t in [0, 1].
     *
     * @param  list<array{t: float, lat: float, lng: float, admin1: string, admin2: string}>  $corridor
     * @return array{0: float, 1: float}
     */
    private function interpolate(array $corridor, float $t): array
    {
        for ($k = 0; $k < count($corridor) - 1; $k++) {
            $a = $corridor[$k];
            $b = $corridor[$k + 1];

            if ($t <= $b['t']) {
                $segSpan = $b['t'] - $a['t'];
                $frac = $segSpan > 0 ? ($t - $a['t']) / $segSpan : 0.0;

                return [
                    $a['lat'] + ($b['lat'] - $a['lat']) * $frac,
                    $a['lng'] + ($b['lng'] - $a['lng']) * $frac,
                ];
            }
        }

        $last = $corridor[count($corridor) - 1];

        return [$last['lat'], $last['lng']];
    }

    /**
     * Find the corridor waypoint whose t is closest to the given parameter.
     *
     * @param  list<array{t: float, lat: float, lng: float, admin1: string, admin2: string}>  $corridor
     * @return array{t: float, lat: float, lng: float, admin1: string, admin2: string}
     */
    private function nearestWaypoint(array $corridor, float $t): array
    {
        $nearest = $corridor[0];

        foreach ($corridor as $waypoint) {
            if (abs($waypoint['t'] - $t) < abs($nearest['t'] - $t)) {
                $nearest = $waypoint;
            }
        }

        return $nearest;
    }

    /**
     * Standard-normal sample via the Box–Muller transform.
     */
    private function gauss(): float
    {
        $u1 = mt_rand(1, mt_getrandmax()) / mt_getrandmax();
        $u2 = mt_rand(0, mt_getrandmax()) / mt_getrandmax();

        return sqrt(-2 * log($u1)) * cos(2 * M_PI * $u2);
    }
}

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
     * Scoring tunables. relevance_score = min(1, proximity + W_DENSITY*density +
     * W_SEVERITY*severity), clamped to [0, 1]. Proximity to Bern is the base signal
     * (an event right next to Bern starts near 1.0; a far-off flyway branch in
     * France, Italy or the Balkans starts near 0), and local density + outbreak
     * severity are smaller bonuses that can only nudge a nearby event upward — they
     * can never lift a distant one. The dashboard bins the score into Rot (>= 0.8) /
     * Orange (>= 0.5) / Grün, and the stored priority enum uses the same thresholds.
     */
    private const PROXIMITY_RADIUS_KM = 120.0;   // proximity decay scale

    private const DENSITY_CELL_DEG = 0.1;        // ~11 km grid cell for the density histogram

    private const DENSITY_FULL = 150;            // neighbour count that saturates the density term

    private const SEVERITY_REF = 500;            // case count that saturates the severity term

    private const W_DENSITY = 0.15;              // max bonus from a dense cluster

    private const W_SEVERITY = 0.15;             // max bonus from a severe outbreak

    private const PRIORITY_HIGH = 0.8;

    private const PRIORITY_MEDIUM = 0.5;

    /**
     * Seed ~10k HPAI (Geflügelpest) outbreak events spreading along several European
     * bird-migration flyways over three months. One stream funnels down through
     * Germany into Switzerland (the operationally relevant branch); the others fan
     * out west into France/Iberia, east into the Black Sea flyway and south into
     * Italy — mirroring how the virus actually disperses with migrating birds.
     *
     * Time is correlated with progress along each stream (early March at the
     * northern start, late May at the destination). Relevance is always measured as
     * proximity to Bern, so the off-axis branches register as low-priority noise.
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

        // Bird-migration flyways. Each stream is a polyline of waypoints (t in [0, 1],
        // early -> late) carrying the virus from a northern start to a destination.
        // 'weight' sets how many events follow the stream; only the Swiss-bound stream
        // snaps onto the lake hotspots below. The non-Swiss streams scatter HPAI across
        // Europe so the map shows a realistic multi-directional spread — but, being far
        // from Bern, they score as low relevance.
        $streams = [
            // Central flyway: Wattenmeer -> Germany -> Swiss plateau (the relevant one).
            [
                'weight' => 5,
                'snapToSwiss' => true,
                'path' => [
                    ['t' => 0.00, 'lat' => 55.30, 'lng' => 8.60, 'admin1' => 'Dänemark', 'admin2' => 'Syddanmark (Wattenmeer)'],
                    ['t' => 0.12, 'lat' => 54.30, 'lng' => 9.00, 'admin1' => 'Schleswig-Holstein', 'admin2' => 'Nordfriesland'],
                    ['t' => 0.25, 'lat' => 53.20, 'lng' => 9.00, 'admin1' => 'Niedersachsen', 'admin2' => 'Bremen/Hamburg'],
                    ['t' => 0.40, 'lat' => 52.00, 'lng' => 9.30, 'admin1' => 'Nordrhein-Westfalen', 'admin2' => 'Ostwestfalen'],
                    ['t' => 0.55, 'lat' => 50.50, 'lng' => 8.70, 'admin1' => 'Hessen', 'admin2' => 'Mittelhessen'],
                    ['t' => 0.70, 'lat' => 49.00, 'lng' => 9.00, 'admin1' => 'Baden-Württemberg', 'admin2' => 'Heilbronn-Franken'],
                    ['t' => 0.85, 'lat' => 47.70, 'lng' => 9.20, 'admin1' => 'Baden-Württemberg', 'admin2' => 'Bodensee'],
                    ['t' => 1.00, 'lat' => 46.95, 'lng' => 7.60, 'admin1' => 'Schweiz', 'admin2' => 'Schweizer Mittelland'],
                ],
            ],
            // East-Atlantic flyway: Netherlands -> France -> Iberia.
            [
                'weight' => 3,
                'snapToSwiss' => false,
                'path' => [
                    ['t' => 0.00, 'lat' => 53.20, 'lng' => 6.50, 'admin1' => 'Niederlande', 'admin2' => 'Friesland'],
                    ['t' => 0.30, 'lat' => 51.00, 'lng' => 3.20, 'admin1' => 'Belgien', 'admin2' => 'Flandern'],
                    ['t' => 0.55, 'lat' => 48.80, 'lng' => 2.30, 'admin1' => 'Frankreich', 'admin2' => 'Île-de-France'],
                    ['t' => 0.78, 'lat' => 45.00, 'lng' => 0.50, 'admin1' => 'Frankreich', 'admin2' => 'Nouvelle-Aquitaine'],
                    ['t' => 1.00, 'lat' => 41.60, 'lng' => 1.60, 'admin1' => 'Spanien', 'admin2' => 'Katalonien'],
                ],
            ],
            // Black-Sea / Mediterranean flyway: Poland -> Austria -> Balkans.
            [
                'weight' => 3,
                'snapToSwiss' => false,
                'path' => [
                    ['t' => 0.00, 'lat' => 54.20, 'lng' => 18.60, 'admin1' => 'Polen', 'admin2' => 'Pommern'],
                    ['t' => 0.30, 'lat' => 50.10, 'lng' => 14.40, 'admin1' => 'Tschechien', 'admin2' => 'Prag'],
                    ['t' => 0.55, 'lat' => 48.20, 'lng' => 16.40, 'admin1' => 'Österreich', 'admin2' => 'Wien/Niederösterreich'],
                    ['t' => 0.78, 'lat' => 47.50, 'lng' => 19.05, 'admin1' => 'Ungarn', 'admin2' => 'Budapest'],
                    ['t' => 1.00, 'lat' => 44.80, 'lng' => 20.45, 'admin1' => 'Serbien', 'admin2' => 'Belgrad'],
                ],
            ],
            // Alpine-southbound flyway: North Germany -> Bavaria -> Po valley.
            [
                'weight' => 2,
                'snapToSwiss' => false,
                'path' => [
                    ['t' => 0.00, 'lat' => 52.50, 'lng' => 13.40, 'admin1' => 'Deutschland', 'admin2' => 'Brandenburg'],
                    ['t' => 0.35, 'lat' => 49.45, 'lng' => 11.07, 'admin1' => 'Bayern', 'admin2' => 'Mittelfranken'],
                    ['t' => 0.60, 'lat' => 47.27, 'lng' => 11.40, 'admin1' => 'Österreich', 'admin2' => 'Tirol'],
                    ['t' => 0.82, 'lat' => 45.46, 'lng' => 9.19, 'admin1' => 'Italien', 'admin2' => 'Lombardei'],
                    ['t' => 1.00, 'lat' => 44.50, 'lng' => 11.34, 'admin1' => 'Italien', 'admin2' => 'Emilia-Romagna'],
                ],
            ],
        ];

        // Expand the stream weights into a flat pick-list (repetition encodes probability).
        $streamPicker = [];
        foreach ($streams as $index => $stream) {
            for ($w = 0; $w < $stream['weight']; $w++) {
                $streamPicker[] = $index;
            }
        }

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
            // Pick a flyway, then a position along it. Skew toward the destination so
            // density builds up at the southern end of each stream.
            $stream = $streams[$streamPicker[array_rand($streamPicker)]];
            $path = $stream['path'];
            $t = (mt_rand(0, mt_getrandmax()) / mt_getrandmax()) ** 0.7;

            // Time follows progress along the stream, with a few days of jitter.
            $offset = (int) round($t * $span + $this->gauss() * 3 * 86400);
            $occurredTs = max(0, min($span, $offset));
            $occurredAt = $start->copy()->addSeconds($occurredTs)->format('Y-m-d H:i:s');

            [$lat, $lng] = $this->interpolate($path, $t);
            $lat += $this->gauss() * 0.35;
            $lng += $this->gauss() * 0.50;

            $population = $populations[array_rand($populations)];

            if ($stream['snapToSwiss'] && $lat <= 47.7) {
                // Swiss band: snap onto a lake hotspot for realistic clustering.
                $hotspot = $swissHotspots[array_rand($swissHotspots)];
                $lat = $hotspot['lat'] + $this->gauss() * $hotspot['spread'];
                $lng = $hotspot['lng'] + $this->gauss() * $hotspot['spread'];
                $admin1 = $hotspot['canton'];
                $admin2 = $hotspot['name'];
            } else {
                $waypoint = $this->nearestWaypoint($path, $t);
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

            $score = min(1.0, $proximity
                + self::W_DENSITY * $density
                + self::W_SEVERITY * $severity);

            $priority = match (true) {
                $score >= self::PRIORITY_HIGH => EventPriority::High,
                $score >= self::PRIORITY_MEDIUM => EventPriority::Medium,
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
                // Commercial poultry flock; a small fraction of the flock falls ill.
                $susceptible = mt_rand(100, 4000);
                $cases = max(1, (int) round($susceptible * (mt_rand(1, 8) / 100)));
                $deaths = mt_rand((int) round($cases * 0.3), $cases);
                break;

            case 'Gehaltene Vögel':
                // Captive / backyard holding; small numbers.
                $susceptible = mt_rand(3, 80);
                $cases = max(1, (int) round($susceptible * (mt_rand(5, 30) / 100)));
                $deaths = mt_rand(0, $cases);
                break;

            default:
                // Wild birds, usually found dead in small numbers (high mortality).
                $susceptible = mt_rand(1, 12);
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

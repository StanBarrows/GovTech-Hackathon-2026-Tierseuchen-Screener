<?php

namespace Database\Seeders;

use App\Models\Species;
use Illuminate\Database\Seeder;

class SpeciesSeeder extends Seeder
{
    /**
     * Seed species lookup (German common names from ADIS data).
     */
    public function run(): void
    {
        foreach ([
            // Vögel
            'Habicht',
            'Habichtartige',
            'Nilgans',
            'Stockente',
            'Entenvögel',
            'Graugans',
            'Kurzschnabelgans',
            'Schneegans',
            'Gänse',
            'Steinadler',
            'Vögel',
            'Ringelgans',
            'Kanadagans',
            'Weißwangengans',
            'Uhu',
            'Mäusebussard',
            'Weißstorch',
            'Störche',
            'Rohrweihe',
            'Taubenvögel',
            'Kolkrabe',
            'Nebelkrähe',
            'Saatkrähe',
            'Dohle',
            'Schwäne',
            'Singschwan',
            'Höckerschwan',
            'Wanderfalke',
            'Falken',
            'Silbermöwe',
            'Mittelmeermöwe',
            'Rotmilan',
            'Kormorane',
            'Dreizehenmöwe',
            // Säugetiere
            'Bienen',
            'Büffel',
            'Katzen',
            'Rinder',
            'Hunde',
            'Hauspferde',
            'Ziegen',
            'Marderhund',
            'Schafe',
            'Schafe/Ziegen',
            'Wildschwein',
            'Hausschweine',
            'Rotfuchs',
            // Fische
            'Regenbogenforelle',
        ] as $name) {
            Species::updateOrCreate(['name' => $name]);
        }
    }
}

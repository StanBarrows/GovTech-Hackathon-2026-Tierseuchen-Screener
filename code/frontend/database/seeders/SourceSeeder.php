<?php

namespace Database\Seeders;

use App\Models\Source;
use Illuminate\Database\Seeder;

class SourceSeeder extends Seeder
{
    /**
     * Seed the known data sources.
     */
    public function run(): void
    {
        $sources = [
            'BLV',
            'Kantonstierarzt',
            'Labor',
            'Tierarzt',
            'Bürger-Meldung',
            'ADIS',
        ];

        foreach ($sources as $name) {
            Source::updateOrCreate(['name' => $name]);
        }
    }
}

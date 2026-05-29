<?php

namespace Database\Seeders;

use App\Models\Disease;
use Illuminate\Database\Seeder;

class DiseaseSeeder extends Seeder
{
    /**
     * Seed the disease lookup.
     */
    public function run(): void
    {
        foreach ([
            'Geflügelpest (HPAI)',
            'Tollwut',
            'Maul- und Klauenseuche',
        ] as $name) {
            Disease::updateOrCreate(['name' => $name]);
        }
    }
}

<?php

namespace Database\Seeders;

use App\Models\Population;
use Illuminate\Database\Seeder;

class PopulationSeeder extends Seeder
{
    /**
     * Seed the population classification lookup.
     */
    public function run(): void
    {
        $populations = ['Wild', 'Nutzgeflügel', 'Gehaltene Vögel'];

        foreach ($populations as $name) {
            Population::updateOrCreate(['name' => $name]);
        }
    }
}

<?php

namespace Database\Seeders;

use App\Models\Subtype;
use Illuminate\Database\Seeder;

class SubtypeSeeder extends Seeder
{
    /**
     * Seed disease subtypes (ADIS "Disease type" values).
     */
    public function run(): void
    {
        $subtypes = ['H5N1', 'H5N5', 'RABV', 'SAT 1'];

        foreach ($subtypes as $name) {
            Subtype::updateOrCreate(['name' => $name]);
        }
    }
}

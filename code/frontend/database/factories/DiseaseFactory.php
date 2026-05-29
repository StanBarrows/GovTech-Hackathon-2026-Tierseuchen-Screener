<?php

namespace Database\Factories;

use App\Models\Disease;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Disease>
 */
class DiseaseFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        $name = fake()->unique()->randomElement([
            'Avian Influenza',
            'African Swine Fever',
            'Foot-and-Mouth Disease',
            'Bluetongue',
            'Bovine Tuberculosis',
            'Rabies',
        ]);

        return [
            'name' => $name,
        ];
    }
}

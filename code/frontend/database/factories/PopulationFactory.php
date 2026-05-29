<?php

namespace Database\Factories;

use App\Models\Population;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Population>
 */
class PopulationFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'name' => fake()->unique()->randomElement(['Domestic', 'Wild', 'Captive', 'Sentinel', 'Poultry']),
        ];
    }
}

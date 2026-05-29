<?php

namespace Database\Factories;

use App\Models\Subtype;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Subtype>
 */
class SubtypeFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'name' => fake()->unique()->randomElement(['H5N1', 'H5N8', 'H5N5', 'H7N9', 'Genotype II']),
        ];
    }
}

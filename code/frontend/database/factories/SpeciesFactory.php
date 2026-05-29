<?php

namespace Database\Factories;

use App\Models\Species;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Species>
 */
class SpeciesFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'name' => fake()->unique()->randomElement([
                'Chicken',
                'Mute Swan',
                'Greylag Goose',
                'Mallard',
                'Domestic Pig',
                'Wild Boar',
            ]),
        ];
    }
}

<?php

namespace Database\Factories;

use App\Enums\EventPriority;
use App\Models\Event;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Event>
 */
class EventFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'disease' => fake()->randomElement(['Geflügelpest (HPAI)', 'Tollwut', 'Maul- und Klauenseuche']),
            'subtype' => fake()->optional()->randomElement(['H5N1', 'H5N8', 'H5N5', 'H7N9']),
            'species' => fake()->optional()->randomElement(['Graugans', 'Höckerschwan', 'Stockente', 'Legehennen-Betrieb']),
            'population' => fake()->optional()->randomElement(['Wild', 'Captive', 'Poultry']),
            'source' => fake()->randomElement(['BLV', 'Kantonstierarzt', 'Labor', 'Tierarzt', 'Bürger-Meldung', 'ADIS']),
            'external_id' => fake()->unique()->bothify('EXT-#####'),
            'occurred_at' => fake()->dateTimeBetween('-1 year'),
            'admin_level_1' => fake()->randomElement(['BE', 'ZH', 'TG', 'VD', 'GE', 'SG']),
            'admin_level_2' => fake()->city(),
            'admin_level_3' => fake()->optional()->streetName(),
            'latitude' => fake()->randomFloat(6, 45.8, 47.8),
            'longitude' => fake()->randomFloat(6, 5.9, 10.5),
            'cases' => fake()->optional()->numberBetween(1, 500),
            'deaths' => fake()->optional()->numberBetween(0, 200),
            'susceptible' => fake()->optional()->numberBetween(0, 5000),
            'distance_km' => fake()->optional()->randomFloat(2, 0, 300),
            'relevance_score' => fake()->optional()->randomFloat(2, 0, 100),
            'priority' => fake()->optional()->randomElement(EventPriority::cases()),
        ];
    }
}

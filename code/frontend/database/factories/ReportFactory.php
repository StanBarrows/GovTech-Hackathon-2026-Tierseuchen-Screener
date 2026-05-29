<?php

namespace Database\Factories;

use App\Models\Report;
use Illuminate\Database\Eloquent\Factories\Factory;

/**
 * @extends Factory<Report>
 */
class ReportFactory extends Factory
{
    /**
     * Define the model's default state.
     *
     * @return array<string, mixed>
     */
    public function definition(): array
    {
        return [
            'source' => fake()->randomElement(['gefluegelnews', 'padi_web']),
            'title' => fake()->sentence(6),
            'url' => fake()->optional()->url(),
            'teaser' => fake()->optional()->sentence(),
            'body' => fake()->optional()->paragraphs(3, true),
            'report_date' => fake()->dateTimeBetween('-1 year')->format('Y-m-d'),
            'admin_level_1' => fake()->randomElement(['BE', 'ZH', 'TG', 'VD', 'GE', 'SG']),
            'admin_level_2' => fake()->optional()->city(),
            'admin_level_3' => null,
            'relevance_score' => fake()->optional()->randomFloat(2, 0, 100),
            'relevance_score_string' => fake()->optional()->randomElement(['high', 'medium', 'low']),
            'distance_km' => fake()->optional()->randomFloat(2, 0, 300),
        ];
    }
}

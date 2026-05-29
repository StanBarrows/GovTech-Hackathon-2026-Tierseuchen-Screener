<?php

namespace App\Models;

use App\Enums\EventPriority;
use Database\Factories\EventFactory;
use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Attributes\Hidden;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;

#[Fillable([
    'disease',
    'subtype',
    'species',
    'population',
    'source',
    'external_id',
    'occurred_at',
    'admin_level_1',
    'admin_level_2',
    'admin_level_3',
    'latitude',
    'longitude',
    'cases',
    'deaths',
    'susceptible',
    'distance_km',
    'relevance_score',
    'priority',
])]
#[Hidden(['distance_km', 'relevance_score', 'priority'])]
class Event extends Model
{
    /** @use HasFactory<EventFactory> */
    use HasFactory;

    /**
     * Get the attributes that should be cast.
     *
     * @return array<string, string>
     */
    protected function casts(): array
    {
        return [
            'occurred_at' => 'datetime',
            'latitude' => 'decimal:6',
            'longitude' => 'decimal:6',
            'distance_km' => 'decimal:2',
            'relevance_score' => 'decimal:2',
            'priority' => EventPriority::class,
        ];
    }

    /**
     * @return BelongsToMany<Report, $this>
     */
    public function reports(): BelongsToMany
    {
        return $this->belongsToMany(Report::class)->withTimestamps();
    }
}

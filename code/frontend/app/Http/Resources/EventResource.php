<?php

namespace App\Http\Resources;

use App\Models\Event;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/**
 * Serialise an Event row into the camelCase "Case" shape the dashboard consumes
 * (see resources/js/types/case.ts). Replaces the former EventDto::toArray().
 *
 * @mixin Event
 */
class EventResource extends JsonResource
{
    /**
     * @return array<string, string|float|null>
     */
    public function toArray(Request $request): array
    {
        return [
            'iri' => "event:{$this->id}",
            'referenceId' => $this->external_id,
            'nationalReferenceId' => null,
            'confirmationDate' => $this->occurred_at?->format('Y-m-d\TH:i'),
            'suspicionStartDate' => null,
            'situationIri' => null,
            'disease' => self::disease($this->disease),
            'diseaseLabel' => $this->disease,
            'subtype' => $this->subtype,
            'subtypeLabel' => $this->subtype,
            'species' => $this->species,
            'speciesLabel' => $this->species,
            'countryLabel' => null,
            'admin1' => $this->admin_level_1,
            'admin2' => $this->admin_level_2,
            'admin3' => $this->admin_level_3,
            'latitude' => $this->latitude !== null ? (float) $this->latitude : null,
            'longitude' => $this->longitude !== null ? (float) $this->longitude : null,
            'population' => self::population($this->population),
            'source' => $this->source,
            'distanceKm' => $this->distance_km !== null ? (float) $this->distance_km : null,
            'radiusKm' => null,
            'relevanceIndex' => $this->relevance_score !== null ? (float) $this->relevance_score : null,
        ];
    }

    /**
     * Normalise the stored population label to the lowercase code the dashboard
     * expects (wild|poultry|captive). Handles the German lookup vocab as well as
     * already-coded values.
     */
    private static function population(?string $value): ?string
    {
        if ($value === null || $value === '') {
            return null;
        }

        return match (mb_strtolower($value)) {
            'wild' => 'wild',
            'poultry', 'nutzgeflügel', 'geflügel' => 'poultry',
            'captive', 'gehaltene vögel' => 'captive',
            default => mb_strtolower($value),
        };
    }

    /**
     * Normalise the stored disease name to the frontend disease code used for
     * map colours, the legend and the disease filter (see disease-colors.ts).
     * Handles the German lookup vocab as well as already-coded values.
     */
    private static function disease(?string $value): ?string
    {
        if ($value === null || $value === '') {
            return null;
        }

        return match (mb_strtolower($value)) {
            'hpai', 'geflügelpest (hpai)', 'geflügelpest' => 'HPAI',
            'mks', 'maul- und klauenseuche' => 'MKS',
            'asp', 'afrikanische schweinepest' => 'ASP',
            'bvd', 'bovine virusdiarrhoe' => 'BVD',
            'bt', 'blauzungenkrankheit' => 'BT',
            default => $value,
        };
    }
}

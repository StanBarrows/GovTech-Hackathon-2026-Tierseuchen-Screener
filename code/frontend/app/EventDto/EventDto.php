<?php

namespace App\EventDto;

use App\Services\Lindas\Dto\OutbreakEvent;
use App\Services\Lindas\IriHelper;

readonly class EventDto
{
    public const DEFAULT_POPULATION = 'wild';

    public const DEFAULT_SOURCE = 'ADIS';

    public function __construct(
        public string $iri,
        public ?string $referenceId,
        public ?string $nationalReferenceId,
        public ?string $confirmationDate,
        public ?string $suspicionStartDate,
        public ?string $situationIri,
        public ?string $disease,
        public ?string $diseaseLabel,
        public ?string $subtype,
        public ?string $subtypeLabel,
        public ?string $species,
        public ?string $speciesLabel,
        public ?string $countryLabel,
        public ?string $admin1,
        public ?string $admin2,
        public ?string $admin3,
        public ?float $latitude,
        public ?float $longitude,
        public ?string $population = self::DEFAULT_POPULATION,
        public ?string $source = self::DEFAULT_SOURCE,
        public ?float $distanceKm = null,
        public ?float $radiusKm = null,
        public ?float $relevanceIndex = null,
    ) {}

    public static function fromOutbreakEvent(OutbreakEvent $event): self
    {
        return new self(
            iri: $event->iri,
            referenceId: $event->referenceId,
            nationalReferenceId: $event->nationalReferenceId,
            confirmationDate: $event->confirmationDate,
            suspicionStartDate: $event->suspicionStartDate,
            situationIri: $event->situationIri,
            disease: $event->disease,
            diseaseLabel: $event->diseaseLabel,
            subtype: $event->subtype,
            subtypeLabel: $event->subtypeLabel,
            species: $event->species,
            speciesLabel: $event->speciesLabel,
            countryLabel: $event->countryLabel,
            admin1: $event->admin1,
            admin2: $event->admin2,
            admin3: $event->admin3,
            latitude: $event->latitude,
            longitude: $event->longitude,
        );
    }

    /**
     * @param  array<string, string|float|null>  $data
     */
    public static function fromArray(array $data): self
    {
        return new self(
            iri: (string) ($data['iri'] ?? ''),
            referenceId: isset($data['referenceId']) ? (string) $data['referenceId'] : null,
            nationalReferenceId: isset($data['nationalReferenceId']) ? (string) $data['nationalReferenceId'] : null,
            confirmationDate: isset($data['confirmationDate']) ? (string) $data['confirmationDate'] : null,
            suspicionStartDate: isset($data['suspicionStartDate']) ? (string) $data['suspicionStartDate'] : null,
            situationIri: isset($data['situationIri']) ? (string) $data['situationIri'] : null,
            disease: isset($data['disease']) ? (string) $data['disease'] : null,
            diseaseLabel: isset($data['diseaseLabel']) ? (string) $data['diseaseLabel'] : null,
            subtype: isset($data['subtype']) ? (string) $data['subtype'] : null,
            subtypeLabel: isset($data['subtypeLabel']) ? (string) $data['subtypeLabel'] : null,
            species: isset($data['species']) ? (string) $data['species'] : null,
            speciesLabel: isset($data['speciesLabel']) ? (string) $data['speciesLabel'] : null,
            countryLabel: isset($data['countryLabel']) ? (string) $data['countryLabel'] : null,
            admin1: isset($data['admin1']) ? (string) $data['admin1'] : null,
            admin2: isset($data['admin2']) ? (string) $data['admin2'] : null,
            admin3: isset($data['admin3']) ? (string) $data['admin3'] : null,
            latitude: isset($data['latitude']) ? (float) $data['latitude'] : null,
            longitude: isset($data['longitude']) ? (float) $data['longitude'] : null,
            population: isset($data['population']) ? (string) $data['population'] : self::DEFAULT_POPULATION,
            source: isset($data['source']) ? (string) $data['source'] : self::DEFAULT_SOURCE,
            distanceKm: isset($data['distanceKm']) ? (float) $data['distanceKm'] : null,
            radiusKm: isset($data['radiusKm']) ? (float) $data['radiusKm'] : null,
            relevanceIndex: isset($data['relevanceIndex']) ? (float) $data['relevanceIndex'] : null,
        );
    }

    public function withRelevance(float $centerLat, float $centerLng, float $radiusKm): self
    {
        if ($this->latitude === null || $this->longitude === null) {
            return $this;
        }

        $distanceKm = EventRelevance::haversineKm($this->latitude, $this->longitude, $centerLat, $centerLng);
        $relevanceIndex = EventRelevance::relevance(1.0, $distanceKm, $radiusKm);

        return new self(
            iri: $this->iri,
            referenceId: $this->referenceId,
            nationalReferenceId: $this->nationalReferenceId,
            confirmationDate: $this->confirmationDate,
            suspicionStartDate: $this->suspicionStartDate,
            situationIri: $this->situationIri,
            disease: $this->disease,
            diseaseLabel: $this->diseaseLabel,
            subtype: $this->subtype,
            subtypeLabel: $this->subtypeLabel,
            species: $this->species,
            speciesLabel: $this->speciesLabel,
            countryLabel: $this->countryLabel,
            admin1: $this->admin1,
            admin2: $this->admin2,
            admin3: $this->admin3,
            latitude: $this->latitude,
            longitude: $this->longitude,
            population: $this->population,
            source: $this->source,
            distanceKm: $distanceKm,
            radiusKm: $radiusKm,
            relevanceIndex: $relevanceIndex,
        );
    }

    /**
     * @return array<string, string|float|null>
     */
    public function toArray(): array
    {
        return [
            'iri' => $this->iri,
            'referenceId' => $this->referenceId,
            'nationalReferenceId' => $this->nationalReferenceId,
            'confirmationDate' => $this->confirmationDate,
            'suspicionStartDate' => $this->suspicionStartDate,
            'situationIri' => $this->situationIri,
            'disease' => $this->disease,
            'diseaseLabel' => IriHelper::label($this->diseaseLabel, $this->disease),
            'subtype' => $this->subtype,
            'subtypeLabel' => IriHelper::label($this->subtypeLabel, $this->subtype),
            'species' => $this->species,
            'speciesLabel' => IriHelper::label($this->speciesLabel, $this->species),
            'countryLabel' => $this->countryLabel,
            'admin1' => $this->admin1,
            'admin2' => $this->admin2,
            'admin3' => $this->admin3,
            'latitude' => $this->latitude,
            'longitude' => $this->longitude,
            'population' => $this->population,
            'source' => $this->source,
            'distanceKm' => $this->distanceKm,
            'radiusKm' => $this->radiusKm,
            'relevanceIndex' => $this->relevanceIndex,
        ];
    }
}

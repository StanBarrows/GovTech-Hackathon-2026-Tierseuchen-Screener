<?php

namespace App\Services\Lindas\Dto;

use App\Services\Lindas\IriHelper;

readonly class OutbreakSituationSummary
{
    public function __construct(
        public string $iri,
        public ?string $key,
        public ?string $disease,
        public ?string $diseaseLabel,
        public ?string $country,
        public ?string $countryLabel,
        public ?string $month,
        public int $eventCount,
    ) {}

    /**
     * @param  array<string, string|int|null>  $data
     */
    public static function fromArray(array $data): self
    {
        return new self(
            iri: (string) ($data['iri'] ?? ''),
            key: isset($data['key']) ? (string) $data['key'] : null,
            disease: isset($data['disease']) ? (string) $data['disease'] : null,
            diseaseLabel: isset($data['diseaseLabel']) ? (string) $data['diseaseLabel'] : null,
            country: isset($data['country']) ? (string) $data['country'] : null,
            countryLabel: isset($data['countryLabel']) ? (string) $data['countryLabel'] : null,
            month: isset($data['month']) ? (string) $data['month'] : null,
            eventCount: (int) ($data['eventCount'] ?? 0),
        );
    }

    /**
     * @return array<string, string|int|null>
     */
    public function toArray(): array
    {
        return [
            'iri' => $this->iri,
            'key' => $this->key,
            'disease' => $this->disease,
            'diseaseLabel' => $this->diseaseLabel ?? IriHelper::localName($this->disease),
            'country' => $this->country,
            'countryLabel' => $this->countryLabel ?? IriHelper::localName($this->country),
            'month' => $this->month,
            'eventCount' => $this->eventCount,
        ];
    }
}

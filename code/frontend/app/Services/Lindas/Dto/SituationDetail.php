<?php

namespace App\Services\Lindas\Dto;

use App\Services\Lindas\IriHelper;

readonly class SituationDetail
{
    /**
     * @param  list<OutbreakEvent>  $events
     */
    public function __construct(
        public string $situationIri,
        public ?string $situationKey,
        public ?string $situationMonth,
        public ?string $situationDisease,
        public ?string $situationCountry,
        public ?string $statementIri,
        public ?string $reportIri,
        public ?string $snippetText,
        public ?string $extractionStatus,
        public ?string $extractionConfidence,
        public ?string $relevanceLevel,
        public ?string $severityLevel,
        public ?string $reachLevel,
        public ?string $preventionText,
        public array $events,
    ) {}

    /**
     * @param  array<string, mixed>  $data
     */
    public static function fromArray(array $data): self
    {
        $events = array_map(
            fn (array $event): OutbreakEvent => OutbreakEvent::fromArray($event),
            $data['events'] ?? [],
        );

        return new self(
            situationIri: (string) ($data['situationIri'] ?? ''),
            situationKey: isset($data['situationKey']) ? (string) $data['situationKey'] : null,
            situationMonth: isset($data['situationMonth']) ? (string) $data['situationMonth'] : null,
            situationDisease: isset($data['situationDisease']) ? (string) $data['situationDisease'] : null,
            situationCountry: isset($data['situationCountry']) ? (string) $data['situationCountry'] : null,
            statementIri: isset($data['statementIri']) ? (string) $data['statementIri'] : null,
            reportIri: isset($data['reportIri']) ? (string) $data['reportIri'] : null,
            snippetText: isset($data['snippetText']) ? (string) $data['snippetText'] : null,
            extractionStatus: isset($data['extractionStatus']) ? (string) $data['extractionStatus'] : null,
            extractionConfidence: isset($data['extractionConfidence']) ? (string) $data['extractionConfidence'] : null,
            relevanceLevel: isset($data['relevanceLevel']) ? (string) $data['relevanceLevel'] : null,
            severityLevel: isset($data['severityLevel']) ? (string) $data['severityLevel'] : null,
            reachLevel: isset($data['reachLevel']) ? (string) $data['reachLevel'] : null,
            preventionText: isset($data['preventionText']) ? (string) $data['preventionText'] : null,
            events: $events,
        );
    }

    /**
     * @return array<string, mixed>
     */
    public function toArray(): array
    {
        return [
            'situationIri' => $this->situationIri,
            'situationKey' => $this->situationKey,
            'situationMonth' => $this->situationMonth,
            'situationDisease' => $this->situationDisease,
            'situationDiseaseLabel' => IriHelper::localName($this->situationDisease),
            'situationCountry' => $this->situationCountry,
            'situationCountryLabel' => IriHelper::localName($this->situationCountry),
            'statementIri' => $this->statementIri,
            'reportIri' => $this->reportIri,
            'snippetText' => $this->snippetText,
            'extractionStatus' => $this->extractionStatus,
            'extractionStatusLabel' => IriHelper::localName($this->extractionStatus),
            'extractionConfidence' => $this->extractionConfidence,
            'extractionConfidenceLabel' => IriHelper::localName($this->extractionConfidence),
            'relevanceLevel' => $this->relevanceLevel,
            'relevanceLevelLabel' => IriHelper::localName($this->relevanceLevel),
            'severityLevel' => $this->severityLevel,
            'severityLevelLabel' => IriHelper::localName($this->severityLevel),
            'reachLevel' => $this->reachLevel,
            'reachLevelLabel' => IriHelper::localName($this->reachLevel),
            'preventionText' => $this->preventionText,
            'events' => array_map(fn (OutbreakEvent $event): array => $event->toArray(), $this->events),
            'eventCount' => count($this->events),
        ];
    }
}

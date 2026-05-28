<?php

namespace App\Services\Lindas\Dto;

use App\Services\Lindas\IriHelper;

readonly class PaffLinkage
{
    public function __construct(
        public string $eventIri,
        public ?string $situationIri,
        public ?string $statementIri,
        public ?string $reportIri,
        public ?string $snippetIri,
        public ?string $relevance,
        public ?string $relevanceLabel,
        public ?string $severity,
        public ?string $severityLabel,
        public ?string $reach,
        public ?string $reachLabel,
        public ?string $prevention,
    ) {}

    /**
     * @param  array<string, string|null>  $data
     */
    public static function fromArray(array $data): self
    {
        return new self(
            eventIri: (string) ($data['eventIri'] ?? ''),
            situationIri: isset($data['situationIri']) ? (string) $data['situationIri'] : null,
            statementIri: isset($data['statementIri']) ? (string) $data['statementIri'] : null,
            reportIri: isset($data['reportIri']) ? (string) $data['reportIri'] : null,
            snippetIri: isset($data['snippetIri']) ? (string) $data['snippetIri'] : null,
            relevance: isset($data['relevance']) ? (string) $data['relevance'] : null,
            relevanceLabel: isset($data['relevanceLabel']) ? (string) $data['relevanceLabel'] : null,
            severity: isset($data['severity']) ? (string) $data['severity'] : null,
            severityLabel: isset($data['severityLabel']) ? (string) $data['severityLabel'] : null,
            reach: isset($data['reach']) ? (string) $data['reach'] : null,
            reachLabel: isset($data['reachLabel']) ? (string) $data['reachLabel'] : null,
            prevention: isset($data['prevention']) ? (string) $data['prevention'] : null,
        );
    }

    /**
     * @return array<string, string|null>
     */
    public function toArray(): array
    {
        return [
            'eventIri' => $this->eventIri,
            'situationIri' => $this->situationIri,
            'statementIri' => $this->statementIri,
            'reportIri' => $this->reportIri,
            'snippetIri' => $this->snippetIri,
            'relevance' => $this->relevance,
            'relevanceLabel' => IriHelper::label($this->relevanceLabel, $this->relevance),
            'severity' => $this->severity,
            'severityLabel' => IriHelper::label($this->severityLabel, $this->severity),
            'reach' => $this->reach,
            'reachLabel' => IriHelper::label($this->reachLabel, $this->reach),
            'prevention' => $this->prevention,
        ];
    }
}

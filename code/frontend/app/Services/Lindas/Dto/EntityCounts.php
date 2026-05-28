<?php

namespace App\Services\Lindas\Dto;

readonly class EntityCounts
{
    public function __construct(
        public int $outbreakEvents = 0,
        public int $outbreakSituations = 0,
        public int $paffReports = 0,
        public int $paffSituationStatements = 0,
        public int $evidenceSnippets = 0,
    ) {}

    /**
     * @param  array<string, int>  $data
     */
    public static function fromArray(array $data): self
    {
        return new self(
            outbreakEvents: (int) ($data['outbreakEvents'] ?? 0),
            outbreakSituations: (int) ($data['outbreakSituations'] ?? 0),
            paffReports: (int) ($data['paffReports'] ?? 0),
            paffSituationStatements: (int) ($data['paffSituationStatements'] ?? 0),
            evidenceSnippets: (int) ($data['evidenceSnippets'] ?? 0),
        );
    }

    /**
     * @return array<string, int>
     */
    public function toArray(): array
    {
        return [
            'outbreakEvents' => $this->outbreakEvents,
            'outbreakSituations' => $this->outbreakSituations,
            'paffReports' => $this->paffReports,
            'paffSituationStatements' => $this->paffSituationStatements,
            'evidenceSnippets' => $this->evidenceSnippets,
        ];
    }
}

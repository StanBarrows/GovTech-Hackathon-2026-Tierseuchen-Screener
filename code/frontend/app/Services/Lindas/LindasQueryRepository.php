<?php

namespace App\Services\Lindas;

use App\Services\Lindas\Dto\EntityCounts;
use App\Services\Lindas\Dto\OutbreakEvent;
use App\Services\Lindas\Dto\OutbreakEventFilter;
use App\Services\Lindas\Dto\OutbreakSituationSummary;
use App\Services\Lindas\Dto\PaffLinkage;
use App\Services\Lindas\Dto\SituationDetail;
use App\Services\Lindas\Mappers\EntityCountsMapper;
use App\Services\Lindas\Mappers\OutbreakEventMapper;
use App\Services\Lindas\Mappers\OutbreakSituationSummaryMapper;
use App\Services\Lindas\Mappers\PaffLinkageMapper;
use App\Services\Lindas\Mappers\SituationDetailMapper;

class LindasQueryRepository
{
    public const DEFAULT_EVENT_IRI = 'https://data.tierseuchen-screener.example.org/data/event_de-hpai-non-p-2026-06u4a';

    public const DEFAULT_REPORT_IRI = 'https://data.tierseuchen-screener.example.org/data/report_paff_2026_05_12';

    public const DEFAULT_SITUATION_IRI = 'https://data.tierseuchen-screener.example.org/data/situation_hpai-non-p-in-wild-birds-deutschland-2026-05';

    public const DEFAULT_STMT_IRI = 'https://data.tierseuchen-screener.example.org/data/stmt_paff_hpai_de_2026_05';

    public function __construct(
        private readonly LindasSparqlService $sparql,
        private readonly EntityCountsMapper $entityCountsMapper,
        private readonly OutbreakSituationSummaryMapper $situationSummaryMapper,
        private readonly OutbreakEventMapper $outbreakEventMapper,
        private readonly PaffLinkageMapper $paffLinkageMapper,
        private readonly SituationDetailMapper $situationDetailMapper,
    ) {}

    public function entityCounts(): EntityCounts
    {
        return $this->entityCountsMapper->map(
            $this->sparql->queryFromFile('01-counts.rq'),
        );
    }

    /**
     * @return list<OutbreakSituationSummary>
     */
    public function situationsWithEventCounts(): array
    {
        return $this->situationSummaryMapper->mapMany(
            $this->sparql->queryFromFile('02-situations-with-event-counts.rq'),
        );
    }

    /**
     * @return list<OutbreakEvent>
     */
    public function outbreakEvents(?OutbreakEventFilter $filter = null): array
    {
        $filter ??= new OutbreakEventFilter;

        $query = $this->sparql->loadQueryFile('05-outbreak-events.rq');

        $query = $this->replacePlaceholder($query, 'limit', (string) max(1, $filter->limit));
        $query = $this->replacePlaceholder($query, 'offset', (string) max(0, $filter->offset));
        $query = $this->replacePlaceholder(
            $query,
            'country_filter',
            $filter->countryIri !== null
                ? "FILTER EXISTS { ?event ts:belongsToSituation ?sitFilter . ?sitFilter ts:situationCountry <{$filter->countryIri}> . }"
                : '',
        );
        $query = $this->replacePlaceholder(
            $query,
            'date_from_filter',
            $filter->dateFrom !== null
                ? "FILTER(?confirmationDate >= \"{$filter->dateFrom}\"^^xsd:date)"
                : '',
        );
        $query = $this->replacePlaceholder(
            $query,
            'date_to_filter',
            $filter->dateTo !== null
                ? "FILTER(?confirmationDate <= \"{$filter->dateTo}\"^^xsd:date)"
                : '',
        );

        return $this->outbreakEventMapper->mapMany(
            $this->sparql->select($query),
        );
    }

    public function eventToPaffLinkage(
        string $eventIri = self::DEFAULT_EVENT_IRI,
    ): ?PaffLinkage {
        $query = $this->sparql->loadQueryFile('03-marker-to-paff-report.rq');
        $query = $this->replaceValuesIri($query, 'event', $eventIri);

        return $this->paffLinkageMapper->map(
            $this->sparql->select($query),
        );
    }

    /**
     * @return list<OutbreakEvent>
     */
    public function paffReportToEvents(
        string $reportIri = self::DEFAULT_REPORT_IRI,
    ): array {
        $query = $this->sparql->loadQueryFile('04-paff-report-to-adis-events.rq');
        $query = $this->replaceValuesIri($query, 'report', $reportIri);

        return $this->outbreakEventMapper->mapMany(
            $this->sparql->select($query),
        );
    }

    public function situationDetail(
        string $situationIri = self::DEFAULT_SITUATION_IRI,
        ?string $statementIri = self::DEFAULT_STMT_IRI,
    ): SituationDetail {
        $query = $this->sparql->loadQueryFile('06-situation-detail.rq');
        $query = $this->replacePlaceholder($query, 'situation_iri', "<{$situationIri}>");
        $query = $this->replacePlaceholder($query, 'stmt_iri', "<{$statementIri}>");

        return $this->situationDetailMapper->map(
            $this->sparql->select($query),
        );
    }

    private function replacePlaceholder(string $query, string $name, string $value): string
    {
        return str_replace("{{{$name}}}", $value, $query);
    }

    private function replaceValuesIri(string $query, string $variable, string $iri): string
    {
        $pattern = '/VALUES\s+\?'.preg_quote($variable, '/').'\s*\{[^}]*\}/s';

        $replacement = "VALUES ?{$variable} {\n      <{$iri}>\n    }";

        $result = preg_replace($pattern, $replacement, $query, 1);

        if ($result === null) {
            throw new LindasSparqlException("Could not replace VALUES for ?{$variable} in query.");
        }

        return $result;
    }
}

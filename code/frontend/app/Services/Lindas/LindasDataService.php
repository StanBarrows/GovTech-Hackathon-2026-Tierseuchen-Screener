<?php

namespace App\Services\Lindas;

use App\Services\Lindas\Dto\EntityCounts;
use App\Services\Lindas\Dto\OutbreakEvent;
use App\Services\Lindas\Dto\OutbreakEventFilter;
use App\Services\Lindas\Dto\OutbreakSituationSummary;
use App\Services\Lindas\Dto\PaffLinkage;
use App\Services\Lindas\Dto\SituationDetail;
use Closure;
use Illuminate\Support\Facades\Cache;

class LindasDataService
{
    private const CACHE_BUST_KEY = 'lindas:cache-bust';

    public function __construct(
        private readonly LindasQueryRepository $repository,
    ) {}

    public function entityCounts(): EntityCounts
    {
        $data = $this->rememberArray(
            'counts',
            fn (): array => $this->repository->entityCounts()->toArray(),
        );

        return EntityCounts::fromArray($data);
    }

    /**
     * @return list<OutbreakSituationSummary>
     */
    public function situationsWithEventCounts(): array
    {
        $rows = $this->rememberArray(
            'situations',
            fn (): array => array_map(
                fn (OutbreakSituationSummary $situation): array => $situation->toArray(),
                $this->repository->situationsWithEventCounts(),
            ),
        );

        return array_map(
            fn (array $row): OutbreakSituationSummary => OutbreakSituationSummary::fromArray($row),
            $rows,
        );
    }

    /**
     * @return list<OutbreakEvent>
     */
    public function outbreakEvents(?OutbreakEventFilter $filter = null): array
    {
        $filter ??= new OutbreakEventFilter;

        $rows = $this->rememberArray(
            'events:'.$this->filterCacheKey($filter),
            fn (): array => array_map(
                fn (OutbreakEvent $event): array => $event->toArray(),
                $this->repository->outbreakEvents($filter),
            ),
        );

        return array_map(
            fn (array $row): OutbreakEvent => OutbreakEvent::fromArray($row),
            $rows,
        );
    }

    public function eventToPaffLinkage(
        string $eventIri = LindasQueryRepository::DEFAULT_EVENT_IRI,
    ): ?PaffLinkage {
        $data = $this->rememberNullableArray(
            'paff-event:'.md5($eventIri),
            fn (): ?array => $this->repository->eventToPaffLinkage($eventIri)?->toArray(),
        );

        return $data === null ? null : PaffLinkage::fromArray($data);
    }

    /**
     * @return list<OutbreakEvent>
     */
    public function paffReportToEvents(
        string $reportIri = LindasQueryRepository::DEFAULT_REPORT_IRI,
    ): array {
        $rows = $this->rememberArray(
            'paff-report:'.md5($reportIri),
            fn (): array => array_map(
                fn (OutbreakEvent $event): array => $event->toArray(),
                $this->repository->paffReportToEvents($reportIri),
            ),
        );

        return array_map(
            fn (array $row): OutbreakEvent => OutbreakEvent::fromArray($row),
            $rows,
        );
    }

    public function situationDetail(
        string $situationIri = LindasQueryRepository::DEFAULT_SITUATION_IRI,
        ?string $statementIri = LindasQueryRepository::DEFAULT_STMT_IRI,
    ): SituationDetail {
        $data = $this->rememberArray(
            'detail:'.md5($situationIri.'|'.$statementIri),
            fn (): array => $this->repository->situationDetail($situationIri, $statementIri)->toArray(),
        );

        return SituationDetail::fromArray($data);
    }

    public function clearCache(): void
    {
        Cache::put(self::CACHE_BUST_KEY, $this->cacheBust() + 1, now()->addYear());
    }

    public function cacheTtl(): int
    {
        return max(0, (int) config('services.lindas.cache_ttl', 900));
    }

    public function cacheEnabled(): bool
    {
        return $this->cacheTtl() > 0;
    }

    /**
     * @return array{
     *     meta: array<string, mixed>,
     *     counts: array<string, int>,
     *     data: array<int|string, mixed>|array<string, mixed>|null
     * }
     */
    public function validationSnapshot(
        string $tab = 'events',
        int $page = 1,
        int $perPage = 50,
    ): array {
        $page = max(1, $page);
        $perPage = max(1, min(200, $perPage));

        return $this->rememberArray(
            "snapshot:{$tab}:{$page}:{$perPage}",
            fn (): array => $this->buildValidationSnapshot($tab, $page, $perPage),
        );
    }

    /**
     * @return array{
     *     meta: array<string, mixed>,
     *     counts: array<string, int>,
     *     data: array<int|string, mixed>|array<string, mixed>|null
     * }
     */
    private function buildValidationSnapshot(string $tab, int $page, int $perPage): array
    {
        $counts = $this->entityCounts();

        $data = match ($tab) {
            'situations' => array_map(
                fn (OutbreakSituationSummary $situation): array => $situation->toArray(),
                $this->situationsWithEventCounts(),
            ),
            'paff' => $this->eventToPaffLinkage()?->toArray(),
            'detail' => $this->situationDetail()->toArray(),
            default => array_map(
                fn (OutbreakEvent $event): array => $event->toArray(),
                $this->outbreakEvents(new OutbreakEventFilter(
                    limit: $perPage,
                    offset: ($page - 1) * $perPage,
                )),
            ),
        };

        return [
            'meta' => [
                'endpoint' => (string) config('services.lindas.sparql_endpoint'),
                'graphUri' => (string) config('services.lindas.graph_uri'),
                'tab' => $tab,
                'page' => $page,
                'perPage' => $perPage,
                'cacheEnabled' => $this->cacheEnabled(),
                'cacheTtl' => $this->cacheTtl(),
                'demoEventIri' => LindasQueryRepository::DEFAULT_EVENT_IRI,
                'demoReportIri' => LindasQueryRepository::DEFAULT_REPORT_IRI,
                'demoSituationIri' => LindasQueryRepository::DEFAULT_SITUATION_IRI,
                'demoStatementIri' => LindasQueryRepository::DEFAULT_STMT_IRI,
            ],
            'counts' => $counts->toArray(),
            'data' => $data,
        ];
    }

    /**
     * @param  Closure(): array<string, mixed>|list<array<string, mixed>>  $callback
     * @return array<string, mixed>|list<array<string, mixed>>
     */
    private function rememberArray(string $suffix, Closure $callback): array
    {
        if (! $this->cacheEnabled()) {
            return $callback();
        }

        $key = $this->cacheKey($suffix);
        $cached = Cache::get($key);

        if (is_array($cached)) {
            return $cached;
        }

        if ($cached !== null) {
            Cache::forget($key);
        }

        $value = $callback();

        Cache::put($key, $value, $this->cacheTtl());

        return $value;
    }

    /**
     * @param  Closure(): ?array<string, mixed>  $callback
     * @return ?array<string, mixed>
     */
    private function rememberNullableArray(string $suffix, Closure $callback): ?array
    {
        if (! $this->cacheEnabled()) {
            return $callback();
        }

        $key = $this->cacheKey($suffix);
        $cached = Cache::get($key);

        if (is_array($cached)) {
            if (($cached['present'] ?? false) === false) {
                return null;
            }

            $value = $cached['value'] ?? null;

            return is_array($value) ? $value : null;
        }

        if ($cached !== null) {
            Cache::forget($key);
        }

        $value = $callback();

        Cache::put($key, [
            'present' => $value !== null,
            'value' => $value,
        ], $this->cacheTtl());

        return $value;
    }

    private function cacheKey(string $suffix): string
    {
        $scope = md5(
            (string) config('services.lindas.sparql_endpoint').'|'.
            (string) config('services.lindas.graph_uri'),
        );

        return "lindas:{$scope}:{$this->cacheBust()}:{$suffix}";
    }

    private function cacheBust(): int
    {
        return (int) Cache::get(self::CACHE_BUST_KEY, 0);
    }

    private function filterCacheKey(OutbreakEventFilter $filter): string
    {
        return md5(json_encode([
            $filter->limit,
            $filter->offset,
            $filter->countryIri,
            $filter->dateFrom,
            $filter->dateTo,
        ], JSON_THROW_ON_ERROR));
    }
}

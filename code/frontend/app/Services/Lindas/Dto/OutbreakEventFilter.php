<?php

namespace App\Services\Lindas\Dto;

readonly class OutbreakEventFilter
{
    public function __construct(
        public int $limit = 50,
        public int $offset = 0,
        public ?string $countryIri = null,
        public ?string $dateFrom = null,
        public ?string $dateTo = null,
    ) {}
}

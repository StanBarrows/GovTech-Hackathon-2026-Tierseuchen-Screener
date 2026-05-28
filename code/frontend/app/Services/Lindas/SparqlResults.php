<?php

namespace App\Services\Lindas;

class SparqlResults
{
    /**
     * @param  array<string, mixed>  $raw
     * @param  list<string>  $vars
     * @param  list<array<string, array<string, mixed>>>  $bindings
     */
    public function __construct(
        public readonly array $raw,
        public readonly array $vars,
        public readonly array $bindings,
    ) {}

    /**
     * @param  array<string, mixed>  $data
     */
    public static function fromArray(array $data): self
    {
        return new self(
            $data,
            $data['head']['vars'] ?? [],
            $data['results']['bindings'] ?? [],
        );
    }

    public function count(): int
    {
        return count($this->bindings);
    }

    /**
     * @return list<array<string, string|int|float|null>>
     */
    public function rows(): array
    {
        return array_map(
            fn (array $binding): array => $this->rowFromBinding($binding),
            $this->bindings,
        );
    }

    /**
     * @return array<string, string|int|float|null>|null
     */
    public function first(): ?array
    {
        $rows = $this->rows();

        return $rows[0] ?? null;
    }

    /**
     * @param  array<string, array<string, mixed>>  $binding
     * @return array<string, string|int|float|null>
     */
    private function rowFromBinding(array $binding): array
    {
        $row = [];

        foreach ($binding as $var => $cell) {
            $key = ltrim($var, '?');
            $row[$key] = self::cellValue($cell);
        }

        return $row;
    }

    /**
     * @param  array<string, mixed>  $cell
     */
    public static function cellValue(array $cell): string|int|float|null
    {
        $value = $cell['value'] ?? null;

        if ($value === null) {
            return null;
        }

        $datatype = $cell['datatype'] ?? null;

        if ($datatype !== null) {
            if (str_contains($datatype, '#integer')) {
                return (int) $value;
            }

            if (str_contains($datatype, '#decimal') || str_contains($datatype, '#double')) {
                return (float) $value;
            }
        }

        return (string) $value;
    }
}

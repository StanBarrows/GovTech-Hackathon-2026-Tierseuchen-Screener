<?php

namespace Database\Seeders;

use App\Models\Report;
use Illuminate\Database\Seeder;
use Illuminate\Support\Carbon;

class ReportsSeeder extends Seeder
{
    /**
     * Insert rows in chunks to keep SQLite happy and fast.
     */
    private const CHUNK = 500;

    /**
     * Seed the reports table from the exported reports CSV.
     *
     * The CSV columns map 1:1 onto the Report model (it is a dump of the table,
     * including id and timestamps), so this is a straight import — we preserve
     * the ids so any later event_report links stay stable.
     */
    public function run(): void
    {
        $path = database_path('sources/disease_reports.csv');

        if (! is_file($path)) {
            $this->command?->warn("ReportsSeeder: {$path} not found, skipping.");

            return;
        }

        Report::query()->delete();

        $file = new \SplFileObject($path);
        $file->setFlags(\SplFileObject::READ_CSV | \SplFileObject::SKIP_EMPTY | \SplFileObject::DROP_NEW_LINE);
        $file->setCsvControl(',', '"', '');

        $header = $file->fgetcsv();
        $columns = array_flip($header);

        $buffer = [];

        while (! $file->eof()) {
            $row = $file->fgetcsv();

            // SplFileObject yields a single [null] for a trailing blank line.
            if (! is_array($row) || $row === [null]) {
                continue;
            }

            $get = fn (string $name): ?string => $this->cell($row, $columns, $name);

            $buffer[] = [
                'id' => $get('id'),
                'source' => $get('source'),
                'title' => $get('title'),
                'url' => $get('url'),
                'teaser' => $get('teaser'),
                'body' => $get('body'),
                'report_date' => Carbon::parse($get('report_date'))->format('Y-m-d'),
                'admin_level_1' => $get('admin_level_1'),
                'admin_level_2' => $get('admin_level_2'),
                'admin_level_3' => $get('admin_level_3'),
                'relevance_score' => $get('relevance_score'),
                'relevance_score_string' => $get('relevance_score_string'),
                'distance_km' => $get('distance_km'),
                'created_at' => $this->timestamp($get('created_at')),
                'updated_at' => $this->timestamp($get('updated_at')),
            ];

            if (count($buffer) >= self::CHUNK) {
                Report::query()->insert($buffer);
                $buffer = [];
            }
        }

        if ($buffer !== []) {
            Report::query()->insert($buffer);
        }
    }

    /**
     * Read a named cell from a CSV row, returning null for missing/blank values.
     *
     * @param  list<string|null>  $row
     * @param  array<string, int>  $columns
     */
    private function cell(array $row, array $columns, string $name): ?string
    {
        $index = $columns[$name] ?? null;

        if ($index === null) {
            return null;
        }

        $value = $row[$index] ?? null;

        if ($value === null) {
            return null;
        }

        $value = trim($value);

        return $value === '' ? null : $value;
    }

    /**
     * Normalise a CSV timestamp to a SQLite-friendly datetime, defaulting to now.
     */
    private function timestamp(?string $value): string
    {
        return Carbon::parse($value ?? 'now')->format('Y-m-d H:i:s');
    }
}

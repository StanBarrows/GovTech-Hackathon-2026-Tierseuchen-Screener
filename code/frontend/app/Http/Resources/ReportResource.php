<?php

namespace App\Http\Resources;

use App\Models\Report;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/**
 * Serialise a Report row into the camelCase shape the dashboard consumes
 * (see resources/js/types/report.ts). Mirrors EventResource.
 *
 * @mixin Report
 */
class ReportResource extends JsonResource
{
    /**
     * @return array<string, string|float|int|null>
     */
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'source' => $this->source,
            'title' => $this->title,
            'url' => $this->url,
            'teaser' => $this->teaser,
            'body' => $this->body,
            'reportDate' => $this->report_date?->format('Y-m-d'),
            'admin1' => $this->admin_level_1,
            'admin2' => $this->admin_level_2,
            'admin3' => $this->admin_level_3,
            'relevanceScore' => $this->relevance_score !== null ? (float) $this->relevance_score : null,
            'relevanceLabel' => $this->relevance_score_string,
        ];
    }
}

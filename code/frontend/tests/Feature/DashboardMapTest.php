<?php

namespace Tests\Feature;

use App\Models\Event;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class DashboardMapTest extends TestCase
{
    use RefreshDatabase;

    private const MAX_HTML_BYTES = 5_242_880;

    public function test_map_initial_html_stays_under_seo_crawler_limit(): void
    {
        Event::factory()->count(100)->create();

        $response = $this->get(route('dashboard.map'));

        $response->assertOk();
        $this->assertLessThan(
            self::MAX_HTML_BYTES,
            strlen($response->getContent()),
            'Initial HTML must stay under the 5 MiB SEO crawler limit.',
        );
    }

    public function test_map_initial_html_does_not_inline_full_case_payload(): void
    {
        Event::factory()->count(50)->create();

        $response = $this->get(route('dashboard.map'));

        $response->assertOk();
        $this->assertStringNotContainsString('"confirmationDate"', $response->getContent());
    }
}

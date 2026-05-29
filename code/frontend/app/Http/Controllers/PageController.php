<?php

namespace App\Http\Controllers;

use App\Support\SeoMeta;
use Inertia\Inertia;
use Inertia\Response;

class PageController extends Controller
{
    public function imprint(): Response
    {
        return Inertia::render('imprint', [
            'seo' => SeoMeta::forPage([
                'title' => 'Impressum',
                'description' => 'Impressum und rechtliche Angaben zum Tierseuchen Screener.',
            ]),
        ]);
    }
}

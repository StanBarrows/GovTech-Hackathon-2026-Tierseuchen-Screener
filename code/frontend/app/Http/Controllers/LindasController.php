<?php

namespace App\Http\Controllers;

use App\Services\Lindas\LindasDataService;
use App\Services\Lindas\LindasSparqlException;
use Illuminate\Http\RedirectResponse;
use Inertia\Inertia;
use Inertia\Response;

class LindasController extends Controller
{
    public function index(LindasDataService $lindas): Response
    {
        $tab = request()->string('tab', 'events')->toString();
        $page = max(1, (int) request()->query('page', 1));
        $perPage = max(1, min(200, (int) request()->query('perPage', 50)));

        if (! in_array($tab, ['events', 'situations', 'paff', 'detail'], true)) {
            $tab = 'events';
        }

        $error = null;
        $snapshot = null;

        try {
            $snapshot = $lindas->validationSnapshot($tab, $page, $perPage);
        } catch (LindasSparqlException $e) {
            $error = $e->getMessage();
            $snapshot = [
                'meta' => [
                    'endpoint' => (string) config('services.lindas.sparql_endpoint'),
                    'graphUri' => (string) config('services.lindas.graph_uri'),
                    'tab' => $tab,
                    'page' => $page,
                    'perPage' => $perPage,
                ],
                'counts' => [
                    'outbreakEvents' => 0,
                    'outbreakSituations' => 0,
                    'paffReports' => 0,
                    'paffSituationStatements' => 0,
                    'evidenceSnippets' => 0,
                ],
                'data' => $tab === 'paff' ? null : [],
            ];
        }

        return Inertia::render('lindas', [
            'snapshot' => $snapshot,
            'error' => $error,
        ]);
    }

    public function clearCache(LindasDataService $lindas): RedirectResponse
    {
        $lindas->clearCache();

        return redirect()->route('lindas', request()->only(['tab', 'page', 'perPage']));
    }
}

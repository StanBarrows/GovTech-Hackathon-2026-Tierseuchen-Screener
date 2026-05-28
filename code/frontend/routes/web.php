<?php

use App\Http\Controllers\DashboardController;
use App\Http\Controllers\LindasController;
use Illuminate\Support\Facades\Route;
use Inertia\Inertia;

Route::redirect('/', '/dashboard/map')->name('home');

Route::get('/dashboard/map', [DashboardController::class, 'map'])->name('dashboard.map');

Route::get('/lindas', [LindasController::class, 'index'])->name('lindas');
Route::post('/lindas/cache/clear', [LindasController::class, 'clearCache'])->name('lindas.cache.clear');

Route::get('/imprint', fn () => Inertia::render('imprint'))->name('imprint');

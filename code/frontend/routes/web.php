<?php

use App\Http\Controllers\DashboardController;
use App\Http\Controllers\PageController;
use Illuminate\Support\Facades\Route;

Route::get('/', [DashboardController::class, 'map'])->name('dashboard.map');

Route::get('imprint', [PageController::class, 'imprint'])->name('imprint');

# Tierseuchen Screener — Frontend

Laravel 13 + Inertia + React 19 + Vite 8 + Tailwind 4, tested with Pest 4.

## Requirements

- PHP 8.3+ & Composer
- Node 20+ & npm

## Setup

```bash
composer setup
```

Runs `composer install`, copies `.env`, generates the app key, migrates the DB, installs npm deps, builds assets.

## Run locally

```bash
composer dev
```

Installs all required packages, herd starts the laravel server, Vite dev server..

Or run pieces individually:

```bash
php artisan serve   # http://localhost:8000
npm run dev         # Vite HMR
```

## Useful scripts

```bash
npm run build         # production build
npm run lint          # eslint --fix
npm run types:check   # tsc --noEmit
npm run format        # prettier
```

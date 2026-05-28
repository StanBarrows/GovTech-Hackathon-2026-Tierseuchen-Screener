# Tierseuchen Screener — Frontend

Laravel 13 + Inertia 3 + React 19 + Vite 8 + Tailwind 4. App name: TS-Scanner. Locale: `de_CH`.

## Stack notes

- PHP 8.3+, Pest 4 for tests, Pint for formatting.
- SQLite at `database/database.sqlite` (Laravel default — do not set `DB_DATABASE` in `.env`, it overrides the path).
- Vite plugins: `@inertiajs/vite` (auto-resolves pages by name), `@laravel/vite-plugin-wayfinder`, `babel-plugin-react-compiler`.
- Tailwind v4 — config lives in `resources/css/app.css` via `@theme`, **not** a JS config file.

## Frontend conventions

- File naming: **kebab-case** for everything under `resources/js/` (matches existing `welcome.tsx`, `dashboard-layout.tsx`).
- Import alias `@/*` → `resources/js/*` (see [tsconfig.json](../tsconfig.json)).
- Indentation: 4 spaces (see `.editorconfig` and existing files).
- Structure:
  - `pages/` — Inertia entry points, one per route, auto-resolved by name from the server (`Inertia::render('dashboard')` → `pages/dashboard.tsx`).
  - `layouts/` — shared shells imported into pages.
  - `components/<feature>/` — feature-scoped sub-components. UI primitives go in `components/ui/`.
  - `lib/` — pure helpers (`cn`, etc.).
- Default export for page components; named exports fine for utilities.
- Pass typed props: define a `Props` type at the top of each page/component.

## Routes & data

- Routes in [routes/web.php](../routes/web.php). Prefer named routes.
- Start with closures for prototyping; promote to `Controller@action` once real data wiring (Eloquent, services) is needed — do not invent controllers prematurely.
- Inertia props should be plain arrays / Eloquent-serialized data, not pre-rendered HTML.

## Commands

- `composer dev` — server + queue + logs + Vite concurrently.
- `composer setup` — first-time install (deps, `.env`, key, migrate, build).
- `npm run lint` / `npm run types:check` / `npm run format` — before pushing non-trivial changes.
- `php artisan test` (or `composer test`) — runs Pint check + Pest.

## Don'ts

- Don't add a `tailwind.config.js` — v4 is CSS-first.
- Don't introduce new state libs (Redux, Zustand) without asking — Inertia props + `useState` cover the current scope.
- Don't commit `database/database.sqlite` or `.env`.
- Don't install npm/composer packages without confirming first.

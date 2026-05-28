import { useEffect, useMemo, useState } from 'react';
import { ArrowUpDown, ChevronLeft, ChevronRight, FileText, Search, Sparkles, X } from 'lucide-react';

import CaseDetailDialog from '@/components/dashboard/case-detail-dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';

type Population = 'wild' | 'poultry' | 'captive';

type Case = {
    id: number | string;
    disease: string;
    population?: Population;
    location: string;
    canton?: string;
    species?: string;
    subtype?: string;
    source?: string;
    lat: number;
    lng: number;
    reportedAt: string;
};

type Priority = 'high' | 'medium' | 'low';

const PAGE_SIZE = 100;
const SOURCE_OPTIONS = ['BLV', 'Kantonstierarzt', 'Labor', 'Tierarzt', 'Bürger-Meldung'];

type Props = {
    cases: Case[];
    centerLat: number;
    centerLng: number;
};

type SortKey = 'priority' | 'reportedAt' | 'distance';

const PRIORITY_LABEL: Record<'high' | 'medium' | 'low', string> = {
    high: 'Hoch',
    medium: 'Mittel',
    low: 'Tief',
};

const PRIORITY_COLOR: Record<'high' | 'medium' | 'low', string> = {
    high: 'bg-red-500',
    medium: 'bg-amber-500',
    low: 'bg-emerald-500',
};

const PRIORITY_ORDER: Record<'high' | 'medium' | 'low', number> = {
    high: 0,
    medium: 1,
    low: 2,
};

const POP_LABEL: Record<Population, string> = {
    wild: 'Wild',
    poultry: 'Poultry',
    captive: 'Captive',
};

function PopulationIcon({ p }: { p?: Population }) {
    if (p === 'wild') {
        return (
            <svg viewBox="0 0 12 12" className="size-3" aria-hidden>
                <polygon points="6,1 11,11 1,11" fill="none" stroke="currentColor" strokeWidth="1.2" />
            </svg>
        );
    }
    if (p === 'poultry') {
        return (
            <svg viewBox="0 0 12 12" className="size-3" aria-hidden>
                <circle cx="6" cy="6" r="4.5" fill="none" stroke="currentColor" strokeWidth="1.2" />
            </svg>
        );
    }
    if (p === 'captive') {
        return (
            <svg viewBox="0 0 12 12" className="size-3" aria-hidden>
                <rect x="1.5" y="1.5" width="9" height="9" fill="none" stroke="currentColor" strokeWidth="1.2" />
            </svg>
        );
    }
    return null;
}

function haversineKm(lat1: number, lng1: number, lat2: number, lng2: number): number {
    const R = 6371;
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLng = ((lng2 - lng1) * Math.PI) / 180;
    const a =
        Math.sin(dLat / 2) ** 2 +
        Math.cos((lat1 * Math.PI) / 180) *
            Math.cos((lat2 * Math.PI) / 180) *
            Math.sin(dLng / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(a));
}

function formatDate(iso: string) {
    const datePart = iso.split('T')[0];
    const [y, m, d] = datePart.split('-');
    const timePart = iso.includes('T') ? ` · ${iso.split('T')[1].slice(0, 5)}` : '';
    return `${d}.${m}.${y.slice(2)}${timePart}`;
}

type DetailRow = Case & { distance: number; priority: 'high' | 'medium' | 'low' };

function escapeHtml(s: string): string {
    return s
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function openReportWindow(rows: DetailRow[]) {
    const win = window.open('', '_blank');
    if (!win) return;

    const total = rows.length;
    const byPriority = { high: 0, medium: 0, low: 0 };
    const byPop: Record<string, number> = {};
    const bySource: Record<string, number> = {};
    const byCanton: Record<string, number> = {};
    for (const r of rows) {
        byPriority[r.priority]++;
        if (r.population) byPop[r.population] = (byPop[r.population] ?? 0) + 1;
        if (r.source) bySource[r.source] = (bySource[r.source] ?? 0) + 1;
        if (r.canton) byCanton[r.canton] = (byCanton[r.canton] ?? 0) + 1;
    }
    const topCantons = Object.entries(byCanton)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5);

    const dates = rows.map((r) => r.reportedAt).sort();
    const dateRange =
        dates.length === 0 ? '—' : `${dates[0].slice(0, 10)} – ${dates[dates.length - 1].slice(0, 10)}`;

    const summary = `Auf Basis von ${total} gefilterten Fällen zeigt sich eine Verteilung von ${byPriority.high} Hoch-, ${byPriority.medium} Mittel- und ${byPriority.low} Tief-Priorität-Meldungen im Zeitraum ${dateRange}. ${
        topCantons.length > 0
            ? `Schwerpunkte liegen in ${topCantons
                  .map(([c, n]) => `${c} (${n})`)
                  .join(', ')}.`
            : ''
    } Empfehlung: Monitoring der Hochrisiko-Standorte fortsetzen, Probenahme in Hotspots intensivieren.`;

    const rowsHtml = rows
        .slice(0, 500)
        .map(
            (r) => `<tr>
            <td>${r.id}</td>
            <td>${PRIORITY_LABEL[r.priority]}</td>
            <td>${formatDate(r.reportedAt)}</td>
            <td>${escapeHtml(r.location)}${r.canton ? ` (${escapeHtml(r.canton)})` : ''}</td>
            <td>${r.population ? POP_LABEL[r.population] : '—'}</td>
            <td>${escapeHtml(r.species ?? '—')}</td>
            <td>${escapeHtml(r.subtype ?? '—')}</td>
            <td>${escapeHtml(r.source ?? '—')}</td>
            <td>${Math.round(r.distance)} km</td>
        </tr>`,
        )
        .join('');

    const now = new Date().toLocaleString('de-CH');

    const html = `<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>TS-Scanner — AI Lagebericht</title>
<style>
    @page { size: A4; margin: 18mm; }
    * { box-sizing: border-box; }
    body { font-family: -apple-system, system-ui, sans-serif; color: #18181b; margin: 24px; line-height: 1.4; }
    h1 { font-size: 22px; margin: 0 0 4px; }
    .meta { color: #71717a; font-size: 11px; margin-bottom: 18px; }
    h2 { font-size: 13px; text-transform: uppercase; letter-spacing: 0.04em; color: #52525b; margin: 18px 0 8px; }
    .cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 14px; }
    .card { border: 1px solid #e4e4e7; border-radius: 6px; padding: 8px 10px; }
    .card .label { font-size: 10px; color: #71717a; text-transform: uppercase; }
    .card .value { font-size: 20px; font-weight: 600; }
    .summary { background: #fafafa; border: 1px solid #e4e4e7; padding: 10px 12px; border-radius: 6px; font-size: 12px; }
    .summary .tag { display: inline-block; background: #18181b; color: #fff; font-size: 9px; padding: 1px 6px; border-radius: 999px; vertical-align: middle; margin-right: 6px; }
    table { width: 100%; border-collapse: collapse; font-size: 10px; margin-top: 6px; }
    th, td { text-align: left; padding: 4px 6px; border-bottom: 1px solid #e4e4e7; }
    th { background: #f4f4f5; font-size: 9px; text-transform: uppercase; letter-spacing: 0.04em; }
    .toolbar { position: fixed; top: 12px; right: 12px; }
    .toolbar button { font-size: 12px; padding: 6px 12px; border: 1px solid #18181b; background: #18181b; color: #fff; border-radius: 4px; cursor: pointer; }
    @media print { .toolbar { display: none; } body { margin: 0; } }
</style>
</head>
<body>
<div class="toolbar"><button onclick="window.print()">Als PDF speichern</button></div>
<h1>TS-Scanner — AI Lagebericht</h1>
<div class="meta">Erstellt: ${escapeHtml(now)} · Zeitraum: ${escapeHtml(dateRange)} · ${total} Meldungen</div>

<div class="cards">
    <div class="card"><div class="label">Total</div><div class="value">${total}</div></div>
    <div class="card"><div class="label">Hoch</div><div class="value" style="color:#dc2626">${byPriority.high}</div></div>
    <div class="card"><div class="label">Mittel</div><div class="value" style="color:#f59e0b">${byPriority.medium}</div></div>
    <div class="card"><div class="label">Tief</div><div class="value" style="color:#10b981">${byPriority.low}</div></div>
</div>

<h2>Zusammenfassung</h2>
<div class="summary"><span class="tag">AI</span>${escapeHtml(summary)}</div>

<h2>Top Kantone</h2>
<table><thead><tr><th>Kanton</th><th>Anzahl</th></tr></thead><tbody>
${topCantons.map(([c, n]) => `<tr><td>${escapeHtml(c)}</td><td>${n}</td></tr>`).join('')}
</tbody></table>

<h2>Quellen</h2>
<table><thead><tr><th>Quelle</th><th>Anzahl</th></tr></thead><tbody>
${Object.entries(bySource)
    .sort((a, b) => b[1] - a[1])
    .map(([s, n]) => `<tr><td>${escapeHtml(s)}</td><td>${n}</td></tr>`)
    .join('')}
</tbody></table>

<h2>Fallliste${rows.length > 500 ? ` (Top 500 von ${rows.length})` : ''}</h2>
<table>
<thead><tr><th>ID</th><th>Priorität</th><th>Datum</th><th>Region</th><th>Typ</th><th>Spezies</th><th>Subtyp</th><th>Quelle</th><th>Distanz</th></tr></thead>
<tbody>${rowsHtml}</tbody>
</table>
</body>
</html>`;

    win.document.open();
    win.document.write(html);
    win.document.close();
    setTimeout(() => win.print(), 400);
}

export default function CaseList({ cases, centerLat, centerLng }: Props) {
    const [sortKey, setSortKey] = useState<SortKey>('priority');
    const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
    const [detail, setDetail] = useState<DetailRow | null>(null);
    const [query, setQuery] = useState('');
    const [priorityFilter, setPriorityFilter] = useState<Priority[]>([]);
    const [sourceFilter, setSourceFilter] = useState<string[]>([]);
    const [page, setPage] = useState(1);
    const [generatingReport, setGeneratingReport] = useState(false);

    const rows = useMemo(() => {
        return cases.map((c) => {
            const distance = haversineKm(centerLat, centerLng, c.lat, c.lng);
            const priority: 'high' | 'medium' | 'low' =
                distance < 50 ? 'high' : distance < 150 ? 'medium' : 'low';
            return { ...c, distance, priority };
        });
    }, [cases, centerLat, centerLng]);

    const filtered = useMemo(() => {
        const q = query.trim().toLowerCase();
        return rows.filter((c) => {
            if (priorityFilter.length > 0 && !priorityFilter.includes(c.priority)) return false;
            if (sourceFilter.length > 0 && (!c.source || !sourceFilter.includes(c.source))) return false;
            if (!q) return true;
            const hay = [
                c.disease,
                c.location,
                c.canton,
                c.species,
                c.subtype,
                c.source,
                c.population ? POP_LABEL[c.population] : undefined,
                PRIORITY_LABEL[c.priority],
                String(c.id),
            ]
                .filter(Boolean)
                .join(' ')
                .toLowerCase();
            return hay.includes(q);
        });
    }, [rows, query, priorityFilter, sourceFilter]);

    const sorted = useMemo(() => {
        const dir = sortDir === 'asc' ? 1 : -1;
        return [...filtered].sort((a, b) => {
            if (sortKey === 'priority') {
                return dir * (PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]);
            }
            if (sortKey === 'distance') return dir * (a.distance - b.distance);
            return dir * (a.reportedAt < b.reportedAt ? -1 : a.reportedAt > b.reportedAt ? 1 : 0);
        });
    }, [filtered, sortKey, sortDir]);

    const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));

    useEffect(() => {
        setPage(1);
    }, [query, priorityFilter, sourceFilter, sortKey, sortDir]);

    useEffect(() => {
        if (page > totalPages) setPage(totalPages);
    }, [page, totalPages]);

    const pageRows = useMemo(
        () => sorted.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
        [sorted, page],
    );

    const togglePriority = (p: Priority) => {
        setPriorityFilter((prev) =>
            prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p],
        );
    };
    const toggleSource = (s: string) => {
        setSourceFilter((prev) =>
            prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s],
        );
    };

    const generateReport = () => {
        setGeneratingReport(true);
        setTimeout(() => {
            openReportWindow(sorted);
            setGeneratingReport(false);
        }, 600);
    };

    const toggleSort = (key: SortKey) => {
        if (sortKey === key) {
            setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
        } else {
            setSortKey(key);
            setSortDir(key === 'reportedAt' ? 'desc' : 'asc');
        }
    };

    const sortIndicator = (key: SortKey) =>
        sortKey === key ? (sortDir === 'asc' ? '↑' : '↓') : null;

    return (
        <div className="flex h-full flex-col overflow-hidden rounded-md border bg-card">
            <div className="flex items-center gap-2 border-b px-3 py-2">
                <div className="relative flex-1">
                    <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                        type="search"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Suche: Ort, Kanton, Spezies, Subtyp, ID…"
                        className="h-9 pl-8"
                    />
                    {query && (
                        <button
                            type="button"
                            onClick={() => setQuery('')}
                            aria-label="Suche zurücksetzen"
                            className="absolute top-1/2 right-2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                        >
                            <X className="size-4" />
                        </button>
                    )}
                </div>
                <span className="text-xs text-muted-foreground tabular-nums">
                    {sorted.length} / {rows.length}
                </span>
                <Button
                    type="button"
                    size="sm"
                    onClick={generateReport}
                    disabled={generatingReport || sorted.length === 0}
                    className="ml-1 h-9 gap-1.5"
                >
                    {generatingReport ? (
                        <>
                            <Sparkles className="size-3.5 animate-pulse" />
                            Generiere…
                        </>
                    ) : (
                        <>
                            <FileText className="size-3.5" />
                            AI Report
                        </>
                    )}
                </Button>
            </div>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b px-3 py-2 text-xs">
                <div className="flex items-center gap-1.5">
                    <span className="font-medium text-muted-foreground uppercase tracking-wider">
                        Priorität:
                    </span>
                    {(['high', 'medium', 'low'] as Priority[]).map((p) => {
                        const active = priorityFilter.includes(p);
                        return (
                            <button
                                key={p}
                                type="button"
                                onClick={() => togglePriority(p)}
                                className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 transition-colors ${
                                    active
                                        ? 'border-foreground bg-foreground text-background'
                                        : 'border-border hover:bg-muted'
                                }`}
                            >
                                <span className={`inline-block size-2 rounded-full ${PRIORITY_COLOR[p]}`} />
                                {PRIORITY_LABEL[p]}
                            </button>
                        );
                    })}
                </div>
                <div className="flex items-center gap-1.5">
                    <span className="font-medium text-muted-foreground uppercase tracking-wider">
                        Quelle:
                    </span>
                    {SOURCE_OPTIONS.map((s) => {
                        const active = sourceFilter.includes(s);
                        return (
                            <button
                                key={s}
                                type="button"
                                onClick={() => toggleSource(s)}
                                className={`rounded-full border px-2.5 py-0.5 transition-colors ${
                                    active
                                        ? 'border-foreground bg-foreground text-background'
                                        : 'border-border hover:bg-muted'
                                }`}
                            >
                                {s}
                            </button>
                        );
                    })}
                </div>
                {(priorityFilter.length > 0 || sourceFilter.length > 0) && (
                    <button
                        type="button"
                        onClick={() => {
                            setPriorityFilter([]);
                            setSourceFilter([]);
                        }}
                        className="ml-auto inline-flex items-center gap-1 text-muted-foreground hover:text-foreground"
                    >
                        <X className="size-3" /> Filter zurücksetzen
                    </button>
                )}
            </div>
            <div className="flex-1 overflow-auto">
            <Table>
                <TableHeader className="sticky top-0 bg-card">
                    <TableRow>
                        <TableHead>
                            <button
                                type="button"
                                onClick={() => toggleSort('priority')}
                                className="inline-flex items-center gap-1 text-xs font-semibold tracking-wider uppercase"
                            >
                                Priorität <ArrowUpDown className="size-3" />
                                {sortIndicator('priority')}
                            </button>
                        </TableHead>
                        <TableHead>
                            <button
                                type="button"
                                onClick={() => toggleSort('reportedAt')}
                                className="inline-flex items-center gap-1 text-xs font-semibold tracking-wider uppercase"
                            >
                                Datum <ArrowUpDown className="size-3" />
                                {sortIndicator('reportedAt')}
                            </button>
                        </TableHead>
                        <TableHead className="text-xs font-semibold tracking-wider uppercase">
                            Region / Ort
                        </TableHead>
                        <TableHead className="text-xs font-semibold tracking-wider uppercase">
                            Typ
                        </TableHead>
                        <TableHead className="text-xs font-semibold tracking-wider uppercase">
                            Spezies
                        </TableHead>
                        <TableHead className="text-xs font-semibold tracking-wider uppercase">
                            Subtype
                        </TableHead>
                        <TableHead className="text-xs font-semibold tracking-wider uppercase">
                            Quelle
                        </TableHead>
                        <TableHead>
                            <button
                                type="button"
                                onClick={() => toggleSort('distance')}
                                className="inline-flex items-center gap-1 text-xs font-semibold tracking-wider uppercase"
                            >
                                Distanz <ArrowUpDown className="size-3" />
                                {sortIndicator('distance')}
                            </button>
                        </TableHead>
                        <TableHead />
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {pageRows.map((c) => (
                        <TableRow key={c.id}>
                            <TableCell>
                                <span className="inline-flex items-center gap-2">
                                    <span
                                        className={`inline-block size-2.5 rounded-full ${PRIORITY_COLOR[c.priority]}`}
                                    />
                                    {PRIORITY_LABEL[c.priority]}
                                </span>
                            </TableCell>
                            <TableCell className="tabular-nums">{formatDate(c.reportedAt)}</TableCell>
                            <TableCell>
                                {c.location}
                                {c.canton && (
                                    <span className="text-muted-foreground"> ({c.canton})</span>
                                )}
                            </TableCell>
                            <TableCell>
                                <span className="inline-flex items-center gap-1.5">
                                    <PopulationIcon p={c.population} />
                                    {c.population ? POP_LABEL[c.population] : '—'}
                                </span>
                            </TableCell>
                            <TableCell>{c.species ?? '—'}</TableCell>
                            <TableCell>{c.subtype ?? '—'}</TableCell>
                            <TableCell>{c.source ?? '—'}</TableCell>
                            <TableCell className="tabular-nums">~{Math.round(c.distance)} km</TableCell>
                            <TableCell className="text-right">
                                <button
                                    type="button"
                                    onClick={() => setDetail(c)}
                                    className="text-sm text-primary hover:underline"
                                >
                                    Details ›
                                </button>
                            </TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
            {sorted.length === 0 && (
                <div className="p-6 text-center text-sm text-muted-foreground">
                    {query ? `Keine Treffer für „${query}“.` : 'Keine Fälle.'}
                </div>
            )}
            </div>
            {sorted.length > 0 && (
                <div className="flex items-center justify-between gap-3 border-t bg-card px-3 py-2 text-xs">
                    <span className="text-muted-foreground tabular-nums">
                        {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, sorted.length)} von{' '}
                        {sorted.length}
                    </span>
                    <div className="flex items-center gap-1">
                        <button
                            type="button"
                            onClick={() => setPage((p) => Math.max(1, p - 1))}
                            disabled={page <= 1}
                            className="inline-flex size-7 items-center justify-center rounded border hover:bg-muted disabled:opacity-40"
                            aria-label="Vorherige Seite"
                        >
                            <ChevronLeft className="size-4" />
                        </button>
                        <span className="px-2 tabular-nums">
                            Seite {page} / {totalPages}
                        </span>
                        <button
                            type="button"
                            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                            disabled={page >= totalPages}
                            className="inline-flex size-7 items-center justify-center rounded border hover:bg-muted disabled:opacity-40"
                            aria-label="Nächste Seite"
                        >
                            <ChevronRight className="size-4" />
                        </button>
                    </div>
                </div>
            )}
            <CaseDetailDialog
                open={detail !== null}
                onOpenChange={(o) => !o && setDetail(null)}
                item={detail}
            />
        </div>
    );
}

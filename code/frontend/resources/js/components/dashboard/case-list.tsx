import { ArrowUpDown, ChevronLeft, ChevronRight, Search, X } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import CaseDetailDialog from '@/components/dashboard/case-detail-dialog';
import { Input } from '@/components/ui/input';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { resolveDistanceKm, resolveRelevance } from '@/lib/case-relevance';
import type { Case, Population, RelevanceContext } from '@/types/case';

type Priority = 'high' | 'medium' | 'low';

const PAGE_SIZE = 100;
const SOURCE_OPTIONS = ['BLV', 'Kantonstierarzt', 'Labor', 'Tierarzt', 'Bürger-Meldung'];

type Props = {
    cases: Case[];
    centerLat: number;
    centerLng: number;
    radiusKm: number;
    relevanceContext?: RelevanceContext | null;
};

type SortKey = 'relevance' | 'priority' | 'reportedAt' | 'distance';

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

function formatDate(iso: string) {
    if (!iso) {
        return '—';
    }

    const datePart = iso.split('T')[0];
    const [y, m, d] = datePart.split('-');
    const timePart = iso.includes('T') ? ` · ${iso.split('T')[1].slice(0, 5)}` : '';

    return `${d}.${m}.${y.slice(2)}${timePart}`;
}

// Display projection of a Case used by the list/report/dialog.
export type DetailRow = {
    raw: Case;
    id: string;
    disease: string;
    population?: Population;
    location: string;
    canton?: string;
    species?: string;
    subtype?: string;
    source?: string;
    lat: number | null;
    lng: number | null;
    reportedAt: string;
    distance: number;
    relevance: number;
    priority: 'high' | 'medium' | 'low';
};

export default function CaseList({ cases, centerLat, centerLng, radiusKm, relevanceContext }: Props) {
    const [sortKey, setSortKey] = useState<SortKey>('relevance');
    const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
    const [detail, setDetail] = useState<DetailRow | null>(null);
    const [query, setQuery] = useState('');
    const [priorityFilter, setPriorityFilter] = useState<Priority[]>([]);
    const [sourceFilter, setSourceFilter] = useState<string[]>([]);
    const [page, setPage] = useState(1);
    const rows = useMemo<DetailRow[]>(() => {
        const center = { lat: centerLat, lng: centerLng };

        return cases.map((c) => {
            const distance = resolveDistanceKm(c, center, radiusKm, relevanceContext);
            const r = resolveRelevance(c, center, radiusKm, relevanceContext);
            const priority: 'high' | 'medium' | 'low' =
                r >= 0.8 ? 'high' : r >= 0.5 ? 'medium' : 'low';

            return {
                raw: c,
                id: c.iri,
                disease: c.diseaseLabel ?? c.disease ?? '',
                population: c.population ?? undefined,
                location: c.admin2 ?? c.admin1 ?? c.countryLabel ?? '',
                canton: c.admin1 ?? undefined,
                species: c.speciesLabel ?? c.species ?? undefined,
                subtype: c.subtypeLabel ?? c.subtype ?? undefined,
                source: c.source ?? undefined,
                lat: c.latitude ?? null,
                lng: c.longitude ?? null,
                reportedAt: c.confirmationDate ?? c.suspicionStartDate ?? '',
                distance,
                relevance: r,
                priority,
            };
        });
    }, [cases, centerLat, centerLng, radiusKm, relevanceContext]);

    const filtered = useMemo(() => {
        const q = query.trim().toLowerCase();

        return rows.filter((c) => {
            if (priorityFilter.length > 0 && !priorityFilter.includes(c.priority)) {
return false;
}

            if (sourceFilter.length > 0 && (!c.source || !sourceFilter.includes(c.source))) {
return false;
}

            if (!q) {
return true;
}

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
            if (sortKey === 'relevance') {
return dir * (a.relevance - b.relevance);
}

            if (sortKey === 'priority') {
                return dir * (PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]);
            }

            if (sortKey === 'distance') {
return dir * (a.distance - b.distance);
}

            return dir * (a.reportedAt < b.reportedAt ? -1 : a.reportedAt > b.reportedAt ? 1 : 0);
        });
    }, [filtered, sortKey, sortDir]);

    const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));

    useEffect(() => {
        setPage(1);
    }, [query, priorityFilter, sourceFilter, sortKey, sortDir]);

    useEffect(() => {
        if (page > totalPages) {
setPage(totalPages);
}
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

    const toggleSort = (key: SortKey) => {
        if (sortKey === key) {
            setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
        } else {
            setSortKey(key);
            setSortDir(key === 'reportedAt' || key === 'relevance' ? 'desc' : 'asc');
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
                                onClick={() => toggleSort('relevance')}
                                className="inline-flex items-center gap-1 text-xs font-semibold tracking-wider uppercase"
                            >
                                Relevanz-Index <ArrowUpDown className="size-3" />
                                {sortIndicator('relevance')}
                            </button>
                        </TableHead>
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
                            <TableCell className="tabular-nums font-medium">
                                {c.relevance.toFixed(2)}
                            </TableCell>
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

import {
    ArrowUpDown,
    ChevronLeft,
    ChevronRight,
    ExternalLink,
    Search,
    X,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Markdown } from '@/components/ui/markdown';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import type { Report } from '@/types/report';

type Props = {
    reports: Report[];
};

type SortKey = 'reportDate' | 'relevance';

const PAGE_SIZE = 100;

const RELEVANCE_LEVELS = ['Hoch', 'Mittel', 'Tief'] as const;
type RelevanceLevel = (typeof RELEVANCE_LEVELS)[number];

const RELEVANCE_COLOR: Record<RelevanceLevel, string> = {
    Hoch: 'bg-red-500',
    Mittel: 'bg-amber-500',
    Tief: 'bg-emerald-500',
};

function relevanceColor(label?: string | null): string {
    return RELEVANCE_COLOR[label as RelevanceLevel] ?? 'bg-muted-foreground';
}

function formatRegion(report: Report): string {
    return [report.admin1, report.admin2].filter(Boolean).join(', ') || '–';
}

export default function ReportsView({ reports }: Props) {
    const [activeReport, setActiveReport] = useState<Report | null>(null);
    const [query, setQuery] = useState('');
    const [sourceFilter, setSourceFilter] = useState<string[]>([]);
    const [relevanceFilter, setRelevanceFilter] = useState<RelevanceLevel[]>(
        [],
    );
    const [sortKey, setSortKey] = useState<SortKey>('relevance');
    const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
    const [page, setPage] = useState(1);

    const sourceOptions = useMemo(() => {
        const set = new Set<string>();

        for (const r of reports) {
            if (r.source) {
                set.add(r.source);
            }
        }

        return Array.from(set).sort((a, b) => a.localeCompare(b, 'de-CH'));
    }, [reports]);

    const filtered = useMemo(() => {
        const q = query.trim().toLowerCase();

        return reports.filter((r) => {
            if (
                sourceFilter.length > 0 &&
                (!r.source || !sourceFilter.includes(r.source))
            ) {
                return false;
            }

            if (relevanceFilter.length > 0) {
                const level = r.relevanceLabel;

                if (
                    !level ||
                    !relevanceFilter.includes(level as RelevanceLevel)
                ) {
                    return false;
                }
            }

            if (!q) {
                return true;
            }

            const hay = [
                r.title,
                r.source,
                r.teaser,
                r.admin1,
                r.admin2,
                r.admin3,
                r.relevanceLabel,
            ]
                .filter(Boolean)
                .join(' ')
                .toLowerCase();

            return hay.includes(q);
        });
    }, [reports, query, sourceFilter, relevanceFilter]);

    const sorted = useMemo(() => {
        const dir = sortDir === 'asc' ? 1 : -1;

        return [...filtered].sort((a, b) => {
            if (sortKey === 'relevance') {
                return (
                    dir * ((a.relevanceScore ?? -1) - (b.relevanceScore ?? -1))
                );
            }

            const av = a.reportDate ?? '';
            const bv = b.reportDate ?? '';

            return dir * (av < bv ? -1 : av > bv ? 1 : 0);
        });
    }, [filtered, sortKey, sortDir]);

    const totalPages = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));

    useEffect(() => {
        setPage(1);
    }, [query, sourceFilter, relevanceFilter, sortKey, sortDir]);

    useEffect(() => {
        if (page > totalPages) {
            setPage(totalPages);
        }
    }, [page, totalPages]);

    const pageRows = useMemo(
        () => sorted.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE),
        [sorted, page],
    );

    const toggleSource = (s: string) => {
        setSourceFilter((prev) =>
            prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s],
        );
    };
    const toggleRelevance = (level: RelevanceLevel) => {
        setRelevanceFilter((prev) =>
            prev.includes(level)
                ? prev.filter((x) => x !== level)
                : [...prev, level],
        );
    };

    const toggleSort = (key: SortKey) => {
        if (sortKey === key) {
            setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
        } else {
            setSortKey(key);
            setSortDir('desc');
        }
    };

    const sortIndicator = (key: SortKey) =>
        sortKey === key ? (sortDir === 'asc' ? '↑' : '↓') : null;

    if (reports.length === 0) {
        return (
            <div className="flex min-h-[40vh] items-center justify-center rounded-md border bg-muted/30 p-4 text-sm text-muted-foreground">
                Keine Berichte im gewählten Zeitraum.
            </div>
        );
    }

    return (
        <div className="flex h-full flex-col overflow-hidden rounded-md border bg-card">
            <div className="flex items-center gap-2 border-b px-3 py-2">
                <div className="relative flex-1">
                    <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                        type="search"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Suche: Titel, Quelle, Region…"
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
                    {sorted.length} / {reports.length}
                </span>
            </div>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b px-3 py-2 text-xs">
                <div className="flex items-center gap-1.5">
                    <span className="font-medium tracking-wider text-muted-foreground uppercase">
                        Relevanz:
                    </span>
                    {RELEVANCE_LEVELS.map((level) => {
                        const active = relevanceFilter.includes(level);

                        return (
                            <button
                                key={level}
                                type="button"
                                onClick={() => toggleRelevance(level)}
                                className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 transition-colors ${
                                    active
                                        ? 'border-foreground bg-foreground text-background'
                                        : 'border-border hover:bg-muted'
                                }`}
                            >
                                <span
                                    className={`inline-block size-2 rounded-full ${RELEVANCE_COLOR[level]}`}
                                />
                                {level}
                            </button>
                        );
                    })}
                </div>
                {sourceOptions.length > 0 && (
                    <div className="flex items-center gap-1.5">
                        <span className="font-medium tracking-wider text-muted-foreground uppercase">
                            Quelle:
                        </span>
                        {sourceOptions.map((s) => {
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
                )}
                {(sourceFilter.length > 0 || relevanceFilter.length > 0) && (
                    <button
                        type="button"
                        onClick={() => {
                            setSourceFilter([]);
                            setRelevanceFilter([]);
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
                            <TableHead className="w-[1%] whitespace-nowrap">
                                <button
                                    type="button"
                                    onClick={() => toggleSort('reportDate')}
                                    className="inline-flex items-center gap-1 text-xs font-semibold tracking-wider uppercase"
                                >
                                    Datum <ArrowUpDown className="size-3" />
                                    {sortIndicator('reportDate')}
                                </button>
                            </TableHead>
                            <TableHead className="text-xs font-semibold tracking-wider uppercase">
                                Quelle
                            </TableHead>
                            <TableHead className="text-xs font-semibold tracking-wider uppercase">
                                Titel
                            </TableHead>
                            <TableHead className="text-xs font-semibold tracking-wider uppercase">
                                Region
                            </TableHead>
                            <TableHead>
                                <button
                                    type="button"
                                    onClick={() => toggleSort('relevance')}
                                    className="inline-flex items-center gap-1 text-xs font-semibold tracking-wider uppercase"
                                >
                                    Relevanz <ArrowUpDown className="size-3" />
                                    {sortIndicator('relevance')}
                                </button>
                            </TableHead>
                            <TableHead className="w-[1%] text-right" />
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {pageRows.map((r) => (
                            <TableRow key={r.id}>
                                <TableCell className="whitespace-nowrap tabular-nums">
                                    {r.reportDate ?? '–'}
                                </TableCell>
                                <TableCell className="text-muted-foreground">
                                    {r.source ?? '–'}
                                </TableCell>
                                <TableCell
                                    className="max-w-md truncate"
                                    title={r.title}
                                >
                                    {r.title}
                                </TableCell>
                                <TableCell>{formatRegion(r)}</TableCell>
                                <TableCell>
                                    {r.relevanceLabel ? (
                                        <Badge
                                            variant="outline"
                                            className="gap-1.5"
                                        >
                                            <span
                                                className={`inline-block size-2 rounded-full ${relevanceColor(
                                                    r.relevanceLabel,
                                                )}`}
                                            />
                                            {r.relevanceLabel}
                                        </Badge>
                                    ) : (
                                        '–'
                                    )}
                                </TableCell>
                                <TableCell className="text-right">
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => setActiveReport(r)}
                                    >
                                        Details
                                    </Button>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
                {sorted.length === 0 && (
                    <div className="p-6 text-center text-sm text-muted-foreground">
                        {query
                            ? `Keine Treffer für „${query}“.`
                            : 'Keine Berichte.'}
                    </div>
                )}
            </div>
            {sorted.length > 0 && (
                <div className="flex items-center justify-between gap-3 border-t bg-card px-3 py-2 text-xs">
                    <span className="text-muted-foreground tabular-nums">
                        {(page - 1) * PAGE_SIZE + 1}–
                        {Math.min(page * PAGE_SIZE, sorted.length)} von{' '}
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
                            onClick={() =>
                                setPage((p) => Math.min(totalPages, p + 1))
                            }
                            disabled={page >= totalPages}
                            className="inline-flex size-7 items-center justify-center rounded border hover:bg-muted disabled:opacity-40"
                            aria-label="Nächste Seite"
                        >
                            <ChevronRight className="size-4" />
                        </button>
                    </div>
                </div>
            )}

            <Dialog
                open={activeReport !== null}
                onOpenChange={(open) => {
                    if (!open) {
                        setActiveReport(null);
                    }
                }}
            >
                <DialogContent className="sm:max-w-4xl">
                    {activeReport && (
                        <>
                            <DialogHeader>
                                <DialogTitle>{activeReport.title}</DialogTitle>
                                <DialogDescription>
                                    Berichtsdatum:{' '}
                                    {activeReport.reportDate ?? '–'}
                                    {activeReport.source
                                        ? ` · Quelle: ${activeReport.source}`
                                        : ''}
                                    {formatRegion(activeReport) !== '–'
                                        ? ` · Region: ${formatRegion(activeReport)}`
                                        : ''}
                                </DialogDescription>
                                {activeReport.url && (
                                    <Button
                                        asChild
                                        variant="outline"
                                        size="sm"
                                        className="mt-2 w-fit"
                                    >
                                        <a
                                            href={activeReport.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                        >
                                            Quelle öffnen
                                            <ExternalLink className="size-3.5" />
                                        </a>
                                    </Button>
                                )}
                            </DialogHeader>

                            <div className="mt-2 max-h-[70vh] space-y-4 overflow-auto">
                                {activeReport.teaser && (
                                    <p className="text-sm font-medium text-foreground">
                                        {activeReport.teaser}
                                    </p>
                                )}
                                {activeReport.body && (
                                    <Markdown>{activeReport.body}</Markdown>
                                )}
                            </div>
                        </>
                    )}
                </DialogContent>
            </Dialog>
        </div>
    );
}

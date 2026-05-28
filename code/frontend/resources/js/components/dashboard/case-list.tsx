import { useMemo, useState } from 'react';
import { ArrowUpDown } from 'lucide-react';

import CaseDetailDialog from '@/components/dashboard/case-detail-dialog';
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
    lat: number;
    lng: number;
    reportedAt: string;
};

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

export default function CaseList({ cases, centerLat, centerLng }: Props) {
    const [sortKey, setSortKey] = useState<SortKey>('priority');
    const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
    const [detail, setDetail] = useState<DetailRow | null>(null);

    const rows = useMemo(() => {
        return cases.map((c) => {
            const distance = haversineKm(centerLat, centerLng, c.lat, c.lng);
            const priority: 'high' | 'medium' | 'low' =
                distance < 50 ? 'high' : distance < 150 ? 'medium' : 'low';
            return { ...c, distance, priority };
        });
    }, [cases, centerLat, centerLng]);

    const sorted = useMemo(() => {
        const dir = sortDir === 'asc' ? 1 : -1;
        return [...rows].sort((a, b) => {
            if (sortKey === 'priority') {
                return dir * (PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]);
            }
            if (sortKey === 'distance') return dir * (a.distance - b.distance);
            return dir * (a.reportedAt < b.reportedAt ? -1 : a.reportedAt > b.reportedAt ? 1 : 0);
        });
    }, [rows, sortKey, sortDir]);

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
        <div className="h-full overflow-auto rounded-md border bg-card">
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
                    {sorted.map((c) => (
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
            <CaseDetailDialog
                open={detail !== null}
                onOpenChange={(o) => !o && setDetail(null)}
                item={detail}
            />
        </div>
    );
}

import { useMemo } from 'react';

import { DISEASE_COLORS, DISEASE_FALLBACK  } from '@/components/map/disease-colors';
import type {DiseaseCode} from '@/components/map/disease-colors';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { resolveRelevance } from '@/lib/case-relevance';
import type { Case, Population, RelevanceContext } from '@/types/case';

type Props = {
    cases: Case[];
    centerLat: number;
    centerLng: number;
    radiusKm: number;
    relevanceContext?: RelevanceContext | null;
};

function fmt(v: number): string {
    return v.toFixed(1);
}

const POP_LABELS: Record<Population, string> = {
    wild: 'Wild',
    poultry: 'Poultry',
    captive: 'Captive',
};

const POP_COLORS: Record<Population, string> = {
    wild: '#16a34a',
    poultry: '#f59e0b',
    captive: '#0ea5e9',
};

function diseaseColor(d: string): string {
    return (DISEASE_COLORS as Record<string, string>)[d] ?? DISEASE_FALLBACK;
}

function dayKey(iso: string): string {
    return iso.slice(0, 10);
}

function formatDayShort(key: string): string {
    const [, m, d] = key.split('-');

    return `${d}.${m}`;
}

type Counted<T extends string> = { key: T; label: string; count: number; color: string };

function BarRow({ label, count, max, color }: { label: string; count: number; max: number; color: string }) {
    const pct = max > 0 ? (count / max) * 100 : 0;

    return (
        <div className="space-y-1">
            <div className="flex items-center justify-between text-xs">
                <span className="truncate">{label}</span>
                <span className="tabular-nums text-muted-foreground">{fmt(count)}</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                <div
                    className="h-full rounded-full transition-[width]"
                    style={{ width: `${pct}%`, backgroundColor: color }}
                />
            </div>
        </div>
    );
}

function Donut({ data, total }: { data: Counted<string>[]; total: number }) {
    const size = 140;
    const stroke = 22;
    const r = (size - stroke) / 2;
    const c = 2 * Math.PI * r;
    let offset = 0;
    const segments = data.map((d) => {
        const frac = total > 0 ? d.count / total : 0;
        const len = frac * c;
        const seg = (
            <circle
                key={d.key}
                cx={size / 2}
                cy={size / 2}
                r={r}
                fill="none"
                stroke={d.color}
                strokeWidth={stroke}
                strokeDasharray={`${len} ${c - len}`}
                strokeDashoffset={-offset}
                transform={`rotate(-90 ${size / 2} ${size / 2})`}
            />
        );
        offset += len;

        return seg;
    });

    return (
        <div className="flex items-center gap-4">
            <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden>
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={r}
                    fill="none"
                    stroke="var(--muted)"
                    strokeWidth={stroke}
                    opacity={0.3}
                />
                {segments}
                <text
                    x={size / 2}
                    y={size / 2}
                    textAnchor="middle"
                    dominantBaseline="central"
                    className="fill-foreground"
                    style={{ fontSize: 24, fontWeight: 600 }}
                >
                    {fmt(total)}
                </text>
            </svg>
            <ul className="space-y-1 text-xs">
                {data.map((d) => (
                    <li key={d.key} className="flex items-center gap-2">
                        <span className="inline-block size-2.5 rounded-sm" style={{ backgroundColor: d.color }} />
                        <span className="min-w-16">{d.label}</span>
                        <span className="tabular-nums text-muted-foreground">
                            {fmt(d.count)} ({total > 0 ? Math.round((d.count / total) * 100) : 0}%)
                        </span>
                    </li>
                ))}
            </ul>
        </div>
    );
}

function TimeSeries({ buckets }: { buckets: { key: string; count: number }[] }) {
    const w = 600;
    const h = 180;
    const padL = 28;
    const padB = 22;
    const padT = 8;
    const padR = 8;
    const innerW = w - padL - padR;
    const innerH = h - padT - padB;
    const max = Math.max(1, ...buckets.map((b) => b.count));
    const n = Math.max(buckets.length, 1);
    const barW = (innerW / n) * 0.7;
    const step = innerW / n;

    const ticks = 4;
    const tickVals = Array.from({ length: ticks + 1 }, (_, i) => (max * i) / ticks);

    const labelEvery = Math.max(1, Math.ceil(n / 8));

    return (
        <svg viewBox={`0 0 ${w} ${h}`} className="w-full" preserveAspectRatio="none" role="img">
            {tickVals.map((v) => {
                const y = padT + innerH - (v / max) * innerH;

                return (
                    <g key={v}>
                        <line
                            x1={padL}
                            x2={w - padR}
                            y1={y}
                            y2={y}
                            stroke="currentColor"
                            opacity={0.1}
                        />
                        <text
                            x={padL - 4}
                            y={y}
                            textAnchor="end"
                            dominantBaseline="central"
                            fontSize={9}
                            className="fill-muted-foreground"
                        >
                            {v.toFixed(1)}
                        </text>
                    </g>
                );
            })}
            {buckets.map((b, i) => {
                const barH = (b.count / max) * innerH;
                const x = padL + i * step + (step - barW) / 2;
                const y = padT + innerH - barH;

                return (
                    <g key={b.key}>
                        <rect x={x} y={y} width={barW} height={barH} rx={1.5} className="fill-primary" />
                        {i % labelEvery === 0 && (
                            <text
                                x={x + barW / 2}
                                y={h - 6}
                                textAnchor="middle"
                                fontSize={9}
                                className="fill-muted-foreground"
                            >
                                {formatDayShort(b.key)}
                            </text>
                        )}
                    </g>
                );
            })}
        </svg>
    );
}

export default function StatsView({ cases, centerLat, centerLng, radiusKm, relevanceContext }: Props) {
    const scored = useMemo(() => {
        const center = { lat: centerLat, lng: centerLng };

        return cases.map((c) => ({ c, r: resolveRelevance(c, center, radiusKm, relevanceContext) }));
    }, [cases, centerLat, centerLng, radiusKm, relevanceContext]);

    const total = scored.reduce((s, x) => s + x.r, 0);

    const byDisease = useMemo<Counted<string>[]>(() => {
        const map = new Map<string, number>();

        for (const { c, r } of scored) {
{
    const k = c.diseaseLabel ?? c.disease ?? '—';
    map.set(k, (map.get(k) ?? 0) + r);
}
}

        return [...map.entries()]
            .map(([key, count]) => ({ key, label: key, count, color: diseaseColor(key) }))
            .sort((a, b) => b.count - a.count);
    }, [scored]);

    const byPopulation = useMemo<Counted<Population>[]>(() => {
        const pops: Population[] = ['wild', 'poultry', 'captive'];
        const sums: Record<Population, number> = { wild: 0, poultry: 0, captive: 0 };

        for (const { c, r } of scored) {
            if (c.population) {
sums[c.population] += r;
}
        }

        return pops
            .map((p) => ({ key: p, label: POP_LABELS[p], count: sums[p], color: POP_COLORS[p] }))
            .filter((d) => d.count > 0);
    }, [scored]);

    const byCanton = useMemo(() => {
        const map = new Map<string, number>();

        for (const { c, r } of scored) {
            const k = c.admin1 ?? '—';
            map.set(k, (map.get(k) ?? 0) + r);
        }

        return [...map.entries()]
            .map(([label, count]) => ({ label, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, 8);
    }, [scored]);

    const bySubtype = useMemo(() => {
        const map = new Map<string, number>();

        for (const { c, r } of scored) {
            const k = c.subtypeLabel ?? c.subtype;

            if (!k) {
                continue;
            }

            map.set(k, (map.get(k) ?? 0) + r);
        }

        return [...map.entries()]
            .map(([label, count]) => ({ label, count }))
            .sort((a, b) => b.count - a.count);
    }, [scored]);

    const timeBuckets = useMemo(() => {
        const dated = scored.filter(({ c }) => c.confirmationDate);

        if (dated.length === 0) {
            return [];
        }

        const map = new Map<string, number>();
        let min = dayKey(dated[0].c.confirmationDate as string);
        let max = min;

        for (const { c, r } of dated) {
            const k = dayKey(c.confirmationDate as string);

            if (k < min) {
min = k;
}

            if (k > max) {
max = k;
}

            map.set(k, (map.get(k) ?? 0) + r);
        }

        const out: { key: string; count: number }[] = [];
        const start = new Date(min);
        const end = new Date(max);

        for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
            const k = d.toISOString().slice(0, 10);
            out.push({ key: k, count: map.get(k) ?? 0 });
        }

        return out;
    }, [scored]);

    const diseaseMax = Math.max(1, ...byDisease.map((d) => d.count));
    const cantonMax = Math.max(1, ...byCanton.map((d) => d.count));
    const subtypeMax = Math.max(1, ...bySubtype.map((d) => d.count));

    if (cases.length === 0) {
        return (
            <div className="flex h-full items-center justify-center rounded-md border bg-card text-sm text-muted-foreground">
                Keine Daten für die aktuellen Filter.
            </div>
        );
    }

    return (
        <div className="grid h-full auto-rows-min grid-cols-1 gap-3 overflow-auto rounded-md md:grid-cols-2 xl:grid-cols-3">
            <Card className="md:col-span-2 xl:col-span-3">
                <CardHeader>
                    <CardTitle className="text-sm">Relevanz-Index pro Tag</CardTitle>
                </CardHeader>
                <CardContent>
                    <TimeSeries buckets={timeBuckets} />
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle className="text-sm">Krankheit</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2.5">
                    {byDisease.map((d) => (
                        <BarRow key={d.key} label={d.label} count={d.count} max={diseaseMax} color={d.color} />
                    ))}
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle className="text-sm">Population</CardTitle>
                </CardHeader>
                <CardContent>
                    {byPopulation.length === 0 ? (
                        <p className="text-xs text-muted-foreground">Keine Angaben.</p>
                    ) : (
                        <Donut data={byPopulation} total={byPopulation.reduce((s, d) => s + d.count, 0)} />
                    )}
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle className="text-sm">Top Regionen</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2.5">
                    {byCanton.map((d) => (
                        <BarRow
                            key={d.label}
                            label={d.label}
                            count={d.count}
                            max={cantonMax}
                            color="#6366f1"
                        />
                    ))}
                </CardContent>
            </Card>

            {bySubtype.length > 0 && (
                <Card className="md:col-span-2 xl:col-span-3">
                    <CardHeader>
                        <CardTitle className="text-sm">Subtypen</CardTitle>
                    </CardHeader>
                    <CardContent className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
                        {bySubtype.map((d) => (
                            <BarRow
                                key={d.label}
                                label={d.label}
                                count={d.count}
                                max={subtypeMax}
                                color="#ec4899"
                            />
                        ))}
                    </CardContent>
                </Card>
            )}
        </div>
    );
}

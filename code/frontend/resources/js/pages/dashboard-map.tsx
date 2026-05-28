import { Head } from '@inertiajs/react';
import { Map as MapIcon, List as ListIcon, BarChart3 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import CaseList from '@/components/dashboard/case-list';
import FilterPanel from '@/components/dashboard/filter-panel';
import LagebildHeader from '@/components/dashboard/lagebild-header';
import PlayBar from '@/components/dashboard/play-bar';
import StatsView from '@/components/dashboard/stats-view';
import CaseMap, { type Case } from '@/components/map/case-map';
import ClientOnly from '@/components/map/client-only';
import DashboardLayout from '@/layouts/dashboard-layout';

type Population = 'wild' | 'poultry' | 'captive';

type MapCase = Case & {
    population?: Population;
    canton?: string;
    species?: string;
    subtype?: string;
};

type Props = { cases: MapCase[] };

const ALL_POPULATIONS: Population[] = ['wild', 'poultry', 'captive'];

const CENTER_COORDS: Record<string, [number, number]> = {
    Bern: [46.9480, 7.4474],
    Zürich: [47.3769, 8.5417],
    Genf: [46.2044, 6.1432],
    Basel: [47.5596, 7.5886],
};

const DEFAULT_FROM = '2026-03-01T00:00';
const DEFAULT_TO = '2026-05-28T23:59';

export default function DashboardMap({ cases }: Props) {
    const [view, setView] = useState<'map' | 'list' | 'stats'>(() => {
        if (typeof window === 'undefined') return 'map';
        const stored = window.localStorage.getItem('ts-scanner:view');
        return stored === 'list' || stored === 'stats' ? stored : 'map';
    });

    useEffect(() => {
        window.localStorage.setItem('ts-scanner:view', view);
    }, [view]);
    const [population, setPopulation] = useState<Population[]>(ALL_POPULATIONS);
    const [dateFrom, setDateFrom] = useState(DEFAULT_FROM);
    const [dateTo, setDateTo] = useState(DEFAULT_TO);
    const [species, setSpecies] = useState('');
    const [subtype, setSubtype] = useState('H5N1');
    const [center, setCenter] = useState('Bern');

    const [playCursor, setPlayCursor] = useState(DEFAULT_TO);
    const [playing, setPlaying] = useState(false);

    const togglePopulation = (p: Population) => {
        setPopulation((prev) =>
            prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p],
        );
    };

    const cursorScrubbed = playCursor !== dateTo;
    const effectiveTo = playing || cursorScrubbed ? playCursor : dateTo;

    const filtered = useMemo(() => {
        return cases.filter((c) => {
            if (c.population && !population.includes(c.population)) return false;
            if (dateFrom && c.reportedAt < dateFrom) return false;
            if (effectiveTo && c.reportedAt > effectiveTo) return false;
            if (subtype && c.subtype !== subtype) return false;
            return true;
        });
    }, [cases, population, dateFrom, effectiveTo, subtype]);

    const [centerLat, centerLng] = CENTER_COORDS[center] ?? CENTER_COORDS.Bern;

    return (
        <DashboardLayout>
            <Head title="TS-Scanner" />
            <LagebildHeader title="TS-Scanner" subtitle="" />
            <div className="flex gap-4 p-4" style={{ height: 'calc(100vh - 3.5rem)' }}>
                <FilterPanel
                    population={population}
                    onTogglePopulation={togglePopulation}
                    dateFrom={dateFrom}
                    dateTo={dateTo}
                    onDateFromChange={setDateFrom}
                    onDateToChange={setDateTo}
                    species={species}
                    onSpeciesChange={setSpecies}
                    subtype={subtype}
                    onSubtypeChange={setSubtype}
                    center={center}
                    onCenterChange={setCenter}
                />
                <div className="flex flex-1 flex-col gap-3 overflow-hidden">
                    <div className="inline-flex w-fit rounded-md border bg-card p-0.5 text-sm">
                        <button
                            type="button"
                            onClick={() => setView('map')}
                            className={`inline-flex items-center gap-1.5 rounded px-3 py-1 ${
                                view === 'map'
                                    ? 'bg-foreground text-background'
                                    : 'text-muted-foreground hover:bg-muted'
                            }`}
                        >
                            <MapIcon className="size-3.5" />
                            Map / Heatmap
                        </button>
                        <button
                            type="button"
                            onClick={() => setView('list')}
                            className={`inline-flex items-center gap-1.5 rounded px-3 py-1 ${
                                view === 'list'
                                    ? 'bg-foreground text-background'
                                    : 'text-muted-foreground hover:bg-muted'
                            }`}
                        >
                            <ListIcon className="size-3.5" />
                            Liste
                        </button>
                        <button
                            type="button"
                            onClick={() => setView('stats')}
                            className={`inline-flex items-center gap-1.5 rounded px-3 py-1 ${
                                view === 'stats'
                                    ? 'bg-foreground text-background'
                                    : 'text-muted-foreground hover:bg-muted'
                            }`}
                        >
                            <BarChart3 className="size-3.5" />
                            Statistik
                        </button>
                    </div>
                    {view === 'map' ? (
                        <div className="relative flex-1 overflow-hidden rounded-md border">
                            <ClientOnly
                                fallback={
                                    <div className="flex h-full items-center justify-center bg-muted/30 text-sm text-muted-foreground">
                                        Karte wird geladen…
                                    </div>
                                }
                            >
                                <CaseMap cases={filtered} />
                            </ClientOnly>
                        </div>
                    ) : view === 'list' ? (
                        <div className="flex-1 overflow-hidden">
                            <CaseList
                                cases={filtered}
                                centerLat={centerLat}
                                centerLng={centerLng}
                            />
                        </div>
                    ) : (
                        <div className="flex-1 overflow-hidden">
                            <StatsView cases={filtered} />
                        </div>
                    )}
                    <PlayBar
                        from={dateFrom}
                        to={dateTo}
                        cursor={playCursor}
                        onCursorChange={setPlayCursor}
                        playing={playing}
                        onTogglePlay={() => {
                            if (!playing && (playCursor >= dateTo || playCursor < dateFrom)) {
                                setPlayCursor(dateFrom);
                            }
                            setPlaying((p) => !p);
                        }}
                        onReset={() => {
                            setPlaying(false);
                            setPlayCursor(dateFrom);
                        }}
                        onSkipToEnd={() => {
                            setPlaying(false);
                            setPlayCursor(dateTo);
                        }}
                    />
                </div>
            </div>
        </DashboardLayout>
    );
}

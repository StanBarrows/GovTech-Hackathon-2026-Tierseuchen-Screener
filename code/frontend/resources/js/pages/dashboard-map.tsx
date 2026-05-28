import { Head } from '@inertiajs/react';
import { Map as MapIcon, List as ListIcon, BarChart3 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import CaseList from '@/components/dashboard/case-list';
import FilterPanel from '@/components/dashboard/filter-panel';
import LagebildHeader from '@/components/dashboard/lagebild-header';
import PlayBar from '@/components/dashboard/play-bar';
import StatsView from '@/components/dashboard/stats-view';
import CaseMap from '@/components/map/case-map';
import type {Case} from '@/components/map/case-map';
import ClientOnly from '@/components/map/client-only';
import type {DiseaseCode} from '@/components/map/disease-colors';
import Legend from '@/components/map/legend';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import DashboardLayout from '@/layouts/dashboard-layout';

type Population = 'wild' | 'poultry' | 'captive';

type MapCase = Case & {
    population?: Population;
    canton?: string;
    species?: string;
    subtype?: string;
};

type Props = { cases: MapCase[] };

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
        if (typeof window === 'undefined') {
return 'map';
}

        const stored = window.localStorage.getItem('ts-scanner:view');

        return stored === 'list' || stored === 'stats' ? stored : 'map';
    });

    useEffect(() => {
        window.localStorage.setItem('ts-scanner:view', view);
    }, [view]);
    const [population, setPopulation] = useState<Population[]>([]);
    const [dateFrom, setDateFrom] = useState(DEFAULT_FROM);
    const [dateTo, setDateTo] = useState(DEFAULT_TO);
    const [species, setSpecies] = useState<string[]>([]);

    const toggleSpecies = (s: string) => {
        setSpecies((prev) =>
            prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s],
        );
    };
    const [subtype, setSubtype] = useState('H5N1');
    const [center, setCenter] = useState('Bern');
    const [radiusKm, setRadiusKm] = useState(50);

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
            if (population.length > 0 && (!c.population || !population.includes(c.population))) {
return false;
}

            if (dateFrom && c.reportedAt < dateFrom) {
return false;
}

            if (effectiveTo && c.reportedAt > effectiveTo) {
return false;
}

            if (subtype && c.subtype !== subtype) {
return false;
}

            if (species.length > 0 && (!c.species || !species.includes(c.species))) {
return false;
}

            return true;
        });
    }, [cases, population, dateFrom, effectiveTo, subtype, species]);

    const speciesOptions = useMemo(() => {
        const set = new Set<string>();

        for (const c of cases) {
            if (c.species) {
set.add(c.species);
}
        }

        return Array.from(set).sort((a, b) => a.localeCompare(b, 'de-CH'));
    }, [cases]);

    const [centerLat, centerLng] = CENTER_COORDS[center] ?? CENTER_COORDS.Bern;

    return (
        <DashboardLayout>
            <Head title="TS-Scanner" />
            <LagebildHeader title="TS-Scanner" subtitle="" />
            <div className="flex flex-col gap-4 p-4 md:flex-row md:h-[calc(100vh-3.5rem)]">
                <FilterPanel
                    population={population}
                    onTogglePopulation={togglePopulation}
                    onResetPopulation={() => setPopulation([])}
                    dateFrom={dateFrom}
                    dateTo={dateTo}
                    onDateFromChange={setDateFrom}
                    onDateToChange={setDateTo}
                    species={species}
                    onToggleSpecies={toggleSpecies}
                    onResetSpecies={() => setSpecies([])}
                    speciesOptions={speciesOptions}
                    subtype={subtype}
                    onSubtypeChange={setSubtype}
                    center={center}
                    onCenterChange={setCenter}
                    radiusKm={radiusKm}
                    onRadiusChange={setRadiusKm}
                />
                <div className="flex min-h-[70vh] flex-1 flex-col gap-3 md:min-h-0 md:overflow-hidden">
                    <Tabs
                        value={view}
                        onValueChange={(v) => setView(v as 'map' | 'list' | 'stats')}
                        className="flex min-h-0 flex-1 flex-col gap-3"
                    >
                        <TabsList>
                            <TabsTrigger value="map">
                                <MapIcon />
                                Map / Heatmap
                            </TabsTrigger>
                            <TabsTrigger value="list">
                                <ListIcon />
                                Liste
                            </TabsTrigger>
                            <TabsTrigger value="stats">
                                <BarChart3 />
                                Statistik
                            </TabsTrigger>
                        </TabsList>
                        <TabsContent value="map" className="flex min-h-0 flex-col">
                            <div className="relative min-h-[60vh] flex-1 overflow-hidden rounded-md border md:min-h-0">
                                <ClientOnly
                                    fallback={
                                        <div className="flex h-full items-center justify-center bg-muted/30 text-sm text-muted-foreground">
                                            Karte wird geladen…
                                        </div>
                                    }
                                >
                                    <CaseMap
                                        cases={filtered}
                                        centerLat={centerLat}
                                        centerLng={centerLng}
                                        radiusKm={radiusKm}
                                    />
                                </ClientOnly>
                                <Legend
                                    diseases={['HPAI' as DiseaseCode]}
                                    center={center}
                                    radiusKm={radiusKm}
                                />
                            </div>
                        </TabsContent>
                        <TabsContent value="list" className="overflow-hidden">
                            <CaseList
                                cases={filtered}
                                centerLat={centerLat}
                                centerLng={centerLng}
                                radiusKm={radiusKm}
                            />
                        </TabsContent>
                        <TabsContent value="stats" className="overflow-hidden">
                            <StatsView
                                cases={filtered}
                                centerLat={centerLat}
                                centerLng={centerLng}
                                radiusKm={radiusKm}
                            />
                        </TabsContent>
                    </Tabs>
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

import { Head } from '@inertiajs/react';
import { Map as MapIcon, List as ListIcon, BarChart3, AlertCircle } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';


import CaseList from '@/components/dashboard/case-list';
import FilterPanel from '@/components/dashboard/filter-panel';
import LagebildHeader from '@/components/dashboard/lagebild-header';
import PlayBar from '@/components/dashboard/play-bar';
import StatsView from '@/components/dashboard/stats-view';
import CaseMap from '@/components/map/case-map';
import ClientOnly from '@/components/map/client-only';
import type {DiseaseCode} from '@/components/map/disease-colors';
import Legend from '@/components/map/legend';
import { PageHead } from '@/components/seo/page-head';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import DashboardLayout from '@/layouts/dashboard-layout';
import type { Case, Population, RelevanceContext } from '@/types/case';

type Totals = {
    outbreakEvents: number;
    outbreakSituations: number;
    paffReports: number;
    paffSituationStatements: number;
    evidenceSnippets: number;
};

type Props = {
    cases: Case[];
    relevanceContext?: RelevanceContext | null;
    error?: string | null;
    totals?: Totals;
    diseaseOptions?: string[];
    speciesOptions?: string[];
    subtypeOptions?: string[];
};

const SWITZERLAND_CENTER: [number, number] = [46.8182, 8.2275];
const SWITZERLAND_RADIUS_KM = 200;


export default function DashboardMap({
    cases,
    relevanceContext,
    error,
    totals,
    diseaseOptions: diseaseOptionsProp,
    speciesOptions: speciesOptionsProp,
    subtypeOptions: subtypeOptionsProp,
}: Props) {
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
    const [dateFrom, setDateFrom] = useState('');
    const [dateTo, setDateTo] = useState('');
    const [disease, setDisease] = useState<string[]>([]);

    const toggleDisease = (d: string) => {
        setDisease((prev) =>
            prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d],
        );
    };
    const [species, setSpecies] = useState<string[]>([]);

    const toggleSpecies = (s: string) => {
        setSpecies((prev) =>
            prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s],
        );
    };
    const [subtype, setSubtype] = useState<string[]>([]);

    const toggleSubtype = (s: string) => {
        setSubtype((prev) =>
            prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s],
        );
    };
    const center = 'Switzerland';
    const radiusKm = SWITZERLAND_RADIUS_KM;

    const [playCursor, setPlayCursor] = useState('');
    const [playing, setPlaying] = useState(false);
    const [speed, setSpeed] = useState(1);

    // Keep the play cursor in sync with dateTo while not actively playing,
    // so changes to dateTo (or dateFrom) don't leave a stale cursor that
    // overrides the filter via effectiveTo.
    useEffect(() => {
        if (!playing) {
            setPlayCursor(dateTo);
        }
    }, [dateFrom, dateTo, playing]);

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

            if (disease.length > 0 && (!c.disease || !disease.includes(c.disease))) {
                return false;
            }

            const date = c.confirmationDate ?? c.suspicionStartDate ?? '';

            if (dateFrom && date && date < dateFrom) {
                return false;
            }

            if (effectiveTo && date && date > effectiveTo) {
                return false;
            }

            const subtypeKey = c.subtypeLabel ?? c.subtype ?? '';

            if (subtype.length > 0 && (!subtypeKey || !subtype.includes(subtypeKey))) {
                return false;
            }

            const speciesKey = c.speciesLabel ?? c.species ?? '';

            if (species.length > 0 && (!speciesKey || !species.includes(speciesKey))) {
                return false;
            }

            return true;
        });
    }, [cases, population, disease, dateFrom, effectiveTo, subtype, species]);

    const derivedSpeciesOptions = useMemo(() => {
        const set = new Set<string>();

        for (const c of cases) {
            const k = c.speciesLabel ?? c.species;

            if (k) {
                set.add(k);
            }
        }

        return Array.from(set).sort((a, b) => a.localeCompare(b, 'de-CH'));
    }, [cases]);

    const derivedSubtypeOptions = useMemo(() => {
        const set = new Set<string>();

        for (const c of cases) {
            const k = c.subtypeLabel ?? c.subtype;

            if (k) {
                set.add(k);
            }
        }

        return Array.from(set).sort((a, b) => a.localeCompare(b, 'de-CH'));
    }, [cases]);

    // Prefer backend-provided lookup vocab; fall back to values present in the data.
    const diseaseOptions = diseaseOptionsProp ?? [];
    const speciesOptions =
        speciesOptionsProp && speciesOptionsProp.length > 0
            ? speciesOptionsProp
            : derivedSpeciesOptions;
    const subtypeOptions =
        subtypeOptionsProp && subtypeOptionsProp.length > 0
            ? subtypeOptionsProp
            : derivedSubtypeOptions;

    const populationOptions = useMemo(() => {
        const set = new Set<Population>();

        for (const c of cases) {
            if (c.population) {
                set.add(c.population);
            }
        }

        return Array.from(set).sort();
    }, [cases]);

    const [centerLat, centerLng] = SWITZERLAND_CENTER;

    return (
        <DashboardLayout>
            <Head title="TS-Scanner" />
            <LagebildHeader
                title="TS-Scanner"
                subtitle={
                    totals
                        ? `${cases.length.toLocaleString('de-CH')} von ${totals.outbreakEvents.toLocaleString('de-CH')} Ereignissen geladen`
                        : ''
                }
            />
            {error && (
                <div className="px-4 pt-4">
                    <Alert variant="destructive">
                        <AlertCircle className="size-4" />
                        <AlertTitle>Datenquelle nicht erreichbar</AlertTitle>
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                </div>
            )}
            <div className="flex flex-col gap-4 p-4 md:flex-row md:h-[calc(100vh-3.5rem)]">
                <FilterPanel
                    disease={disease}
                    onToggleDisease={toggleDisease}
                    onResetDisease={() => setDisease([])}
                    diseaseOptions={diseaseOptions}
                    population={population}
                    onTogglePopulation={togglePopulation}
                    onResetPopulation={() => setPopulation([])}
                    dateFrom={dateFrom}
                    dateTo={dateTo}
                    onDateFromChange={setDateFrom}
                    onDateToChange={setDateTo}
                    onResetDate={() => {
                        setDateFrom('');
                        setDateTo('');
                    }}
                    dateChanged={dateFrom !== '' || dateTo !== ''}
                    species={species}
                    onToggleSpecies={toggleSpecies}
                    onResetSpecies={() => setSpecies([])}
                    speciesOptions={speciesOptions}
                    subtype={subtype}
                    onToggleSubtype={toggleSubtype}
                    onResetSubtype={() => setSubtype([])}
                    subtypeOptions={subtypeOptions}
                    populationOptions={populationOptions}
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
                                        relevanceContext={relevanceContext}
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
                                relevanceContext={relevanceContext}
                            />
                        </TabsContent>
                        <TabsContent value="stats" className="overflow-hidden">
                            <StatsView
                                cases={filtered}
                                centerLat={centerLat}
                                centerLng={centerLng}
                                radiusKm={radiusKm}
                                relevanceContext={relevanceContext}
                            />
                        </TabsContent>
                    </Tabs>
                    <PlayBar
                        from={dateFrom}
                        to={dateTo}
                        cursor={playCursor}
                        onCursorChange={setPlayCursor}
                        speed={speed}
                        onSpeedChange={setSpeed}
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

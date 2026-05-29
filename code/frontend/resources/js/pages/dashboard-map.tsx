import { Deferred, Head } from '@inertiajs/react';
import { Map as MapIcon, List as ListIcon, BarChart3, FileText, AlertCircle } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';


import CaseList from '@/components/dashboard/case-list';
import FilterPanel from '@/components/dashboard/filter-panel';
import LagebildHeader from '@/components/dashboard/lagebild-header';
import PlayBar from '@/components/dashboard/play-bar';
import ReportsView from '@/components/dashboard/reports-view';
import StatsView from '@/components/dashboard/stats-view';
import CaseMap from '@/components/map/case-map';
import ClientOnly from '@/components/map/client-only';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import DashboardLayout from '@/layouts/dashboard-layout';
import type { Case, Population, RelevanceContext } from '@/types/case';
import type { Report } from '@/types/report';

type Props = {
    cases?: Case[];
    reports?: Report[];
    relevanceContext?: RelevanceContext | null;
    error?: string | null;
};

type BodyProps = Omit<Props, 'cases' | 'error'> & {
    cases: Case[];
};

// Operational origin (BLV, Bern) — must match the server's relevanceContext so the
// precomputed, Bern-relative relevance_score is used as-is (see resolveRelevance).
const ORIGIN_CENTER: [number, number] = [46.946461621956566, 7.4442526092578625];
const ORIGIN_RADIUS_KM = 120;

function formatLocal(d: Date, time: string): string {
    const pad = (n: number) => String(n).padStart(2, '0');

    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${time}`;
}

function defaultDateRange(): { from: string; to: string } {
    const to = new Date();
    const from = new Date(to);

    from.setMonth(from.getMonth() - 3);

    return {
        from: formatLocal(from, '00:00'),
        to: formatLocal(to, '23:59'),
    };
}

function CasesLoadingFallback() {
    return (
        <div className="flex min-h-[70vh] flex-1 items-center justify-center bg-muted/30 p-4 text-sm text-muted-foreground">
            Ereignisse werden geladen…
        </div>
    );
}

function ReportsLoadingFallback() {
    return (
        <div className="flex min-h-[40vh] items-center justify-center rounded-md border bg-muted/30 p-4 text-sm text-muted-foreground">
            Berichte werden geladen…
        </div>
    );
}

function DashboardMapBody({
    cases,
    reports,
    relevanceContext,
}: BodyProps) {
    const [view, setView] = useState<'map' | 'list' | 'stats' | 'reports'>(() => {
        if (typeof window === 'undefined') {
            return 'map';
        }

        const stored = window.localStorage.getItem('ts-scanner:view');

        return stored === 'list' || stored === 'stats' || stored === 'reports' ? stored : 'map';
    });

    useEffect(() => {
        window.localStorage.setItem('ts-scanner:view', view);
    }, [view]);
    const [population, setPopulation] = useState<Population[]>([]);
    const defaultRange = useMemo(() => defaultDateRange(), []);
    const [dateFrom, setDateFrom] = useState(defaultRange.from);
    const [dateTo, setDateTo] = useState(defaultRange.to);
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
    const radiusKm = ORIGIN_RADIUS_KM;

    const [playCursor, setPlayCursor] = useState(defaultRange.to);
    const [playing, setPlaying] = useState(false);
    const [speed, setSpeed] = useState(4);

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

    // Reports only carry a report_date — the date range is the only applicable
    // filter. Compare on the date portion (Y-m-d) so a report on the exact
    // boundary day is not dropped by the time suffix on dateFrom/dateTo.
    const filteredReports = useMemo(() => {
        const fromDay = dateFrom.slice(0, 10);
        const toDay = dateTo.slice(0, 10);

        return (reports ?? []).filter((r) => {
            if (!r.reportDate) {
                return true;
            }

            return r.reportDate >= fromDay && r.reportDate <= toDay;
        });
    }, [reports, dateFrom, dateTo]);

    const derivedDiseaseOptions = useMemo(() => {
        const set = new Set<string>();

        for (const c of cases) {
            if (c.disease) {
                set.add(c.disease);
            }
        }

        return Array.from(set).sort((a, b) => a.localeCompare(b, 'de-CH'));
    }, [cases]);

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

    // Options are derived from the loaded cases so they always use the same key
    // the filter predicate compares (e.g. the disease *code* c.disease, not the
    // lookup-table label). Backend *Options props are intentionally unused — they
    // carried a different representation and could never match (see plan).
    const diseaseOptions = derivedDiseaseOptions;
    const speciesOptions = derivedSpeciesOptions;
    const subtypeOptions = derivedSubtypeOptions;

    const populationOptions = useMemo(() => {
        const set = new Set<Population>();

        for (const c of cases) {
            if (c.population) {
                set.add(c.population);
            }
        }

        return Array.from(set).sort();
    }, [cases]);

    const [centerLat, centerLng] = ORIGIN_CENTER;

    return (
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
                    setDateFrom(defaultRange.from);
                    setDateTo(defaultRange.to);
                }}
                dateChanged={dateFrom !== defaultRange.from || dateTo !== defaultRange.to}
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
                    onValueChange={(v) => setView(v as 'map' | 'list' | 'stats' | 'reports')}
                    className="flex min-h-0 flex-1 flex-col gap-3"
                >
                    <div className="flex gap-4 py-1 md:py-0">
                        <TabsList>
                            <TabsTrigger value="map">
                                <MapIcon />
                                Karte
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
                        <TabsList>
                            <TabsTrigger value="reports">
                                <FileText />
                                Reports
                            </TabsTrigger>
                        </TabsList>
                    </div>
                    <TabsContent value="map" className="flex min-h-0 flex-col">
                        <div className="relative h-[500px] flex-1 overflow-hidden rounded-md border md:h-auto md:min-h-0">
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
                    <TabsContent value="reports" className="overflow-hidden">
                        <Deferred data="reports" fallback={<ReportsLoadingFallback />}>
                            <ReportsView reports={filteredReports} />
                        </Deferred>
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
    );
}

export default function DashboardMap({
    cases,
    reports,
    relevanceContext,
    error,
}: Props) {
    return (
        <DashboardLayout>
            <Head title="TS-Scanner" />
            <LagebildHeader title="Tierseuchen Scanner - GovTech2026" />
            {error && (
                <div className="px-4 pt-4">
                    <Alert variant="destructive">
                        <AlertCircle className="size-4" />
                        <AlertTitle>Datenquelle nicht erreichbar</AlertTitle>
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                </div>
            )}
            <Deferred data="cases" fallback={<CasesLoadingFallback />}>
                <DashboardMapBody
                    cases={cases!}
                    reports={reports}
                    relevanceContext={relevanceContext}
                />
            </Deferred>
        </DashboardLayout>
    );
}

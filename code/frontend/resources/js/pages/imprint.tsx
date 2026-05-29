import { Link } from '@inertiajs/react';
import { X } from 'lucide-react';
import { useState } from 'react';

import FilterPanel from '@/components/dashboard/filter-panel';
import LagebildHeader from '@/components/dashboard/lagebild-header';
import { PageHead } from '@/components/seo/page-head';
import DashboardLayout from '@/layouts/dashboard-layout';
import type { SeoMeta } from '@/types/seo';

type Population = 'wild' | 'poultry' | 'captive';

type Props = {
    seo: SeoMeta;
};

export default function Imprint({ seo }: Props) {
    const [population, setPopulation] = useState<Population[]>([]);
    const [dateFrom, setDateFrom] = useState('2026-03-01T00:00');
    const [dateTo, setDateTo] = useState('2026-05-28T23:59');
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
    const togglePopulation = (p: Population) => {
        setPopulation((prev) =>
            prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p],
        );
    };

    return (
        <DashboardLayout>
            <PageHead seo={seo} />
            <LagebildHeader title="TS-Scanner" subtitle="Impressum" />
            <div className="flex gap-4 p-4" style={{ height: 'calc(100vh - 3.5rem)' }}>
                <FilterPanel
                    disease={disease}
                    onToggleDisease={toggleDisease}
                    onResetDisease={() => setDisease([])}
                    diseaseOptions={[]}
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
                    dateChanged={false}
                    species={species}
                    onToggleSpecies={toggleSpecies}
                    onResetSpecies={() => setSpecies([])}
                    speciesOptions={[]}
                    subtype={subtype}
                    onToggleSubtype={toggleSubtype}
                    onResetSubtype={() => setSubtype([])}
                    subtypeOptions={[]}
                    populationOptions={[]}
                />
                <div className="flex flex-1 flex-col overflow-hidden">
                    <div className="relative flex-1 overflow-y-auto rounded-md border bg-card p-8">
                        <Link
                            href="/"
                            aria-label="Schliessen"
                            className="absolute right-4 top-4 inline-flex size-8 items-center justify-center rounded-md border bg-background text-muted-foreground hover:bg-muted hover:text-foreground"
                        >
                            <X className="size-4" />
                        </Link>
                        <div className="max-w-2xl space-y-6 text-sm">
                            <h1 className="text-2xl font-semibold">Impressum</h1>

                            <section className="space-y-2">
                                <h2 className="text-base font-semibold">Information Prototype + MVP</h2>
                                <p className="text-muted-foreground">
                                    Im Rahmen des GovTech Hackathon 2026 entwickeltes Projekt. Es handelt sich um einen Prototypen, der nicht für den produktiven Einsatz bestimmt ist. Alle Daten und Inhalte wurden redaktionell überarbeitet und entsprechend anonymisiert.
                                </p>
                            </section>
                            
                            <section className="space-y-2">
                                <h2 className="text-base font-semibold">Challenge Owner</h2>
                                <p className="text-muted-foreground">
                                    Bundesamt für Lebensmittelsicherheit und Veterinärwesen BLV
                                </p>
                            </section>

                            <section className="space-y-2">
                                <h2 className="text-base font-semibold">Team</h2>
                                <p className="text-muted-foreground">
                                    Aurélie Tschopp, Tobias Blatter, Martin Hertach, Roman Riesen, David Gerner, Patrick Arnecke, Sebastian Bürgin, Christian Huber
                                </p>
                            </section>

                            <section className="space-y-2">
                                <h2 className="text-base font-semibold">Kontakt</h2>
                                <p className="text-muted-foreground">
                                    Bundesamt für Lebensmittelsicherheit und Veterinärwesen (BLV)
                                    <br />
                                    Schwarzenburgstrasse 155, 3003 Bern
                                </p>
                            </section>

                            <section className="space-y-2">
                                <h2 className="text-base font-semibold">Haftungsausschluss</h2>
                                <p className="text-muted-foreground">
                                    Der entwickelte Prototyp dient ausschliesslich Demonstrationszwecken im Rahmen des GovTech Hackathon 2026. Es wird keine Haftung für die Inhalte übernommen.
                                </p>
                            </section>

                            <section className="space-y-2">
                                <h2 className="text-base font-semibold">Links</h2>
                                <ul className="list-disc space-y-1 pl-5">
                                    <li>
                                        <a
                                            href="https://govtech.digisus-lab.ch/project/20"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-primary hover:underline"
                                        >
                                            Challenge - GovTech Hackathon 2026
                                        </a>
                                    </li>
                                    <li>
                                        <a
                                            href="https://www.blv.admin.ch"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-primary hover:underline"
                                        >
                                            Bundesamt für Lebensmittelsicherheit und Veterinärwesen (BLV)
                                        </a>
                                    </li>
                                </ul>
                            </section>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}

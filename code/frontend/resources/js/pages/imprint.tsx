import { Head, Link } from '@inertiajs/react';
import { X } from 'lucide-react';
import { useState } from 'react';

import FilterPanel from '@/components/dashboard/filter-panel';
import LagebildHeader from '@/components/dashboard/lagebild-header';
import DashboardLayout from '@/layouts/dashboard-layout';

type Population = 'wild' | 'poultry' | 'captive';

const ALL_POPULATIONS: Population[] = ['wild', 'poultry', 'captive'];

export default function Imprint() {
    const [population, setPopulation] = useState<Population[]>(ALL_POPULATIONS);
    const [dateFrom, setDateFrom] = useState('2026-03-01T00:00');
    const [dateTo, setDateTo] = useState('2026-05-28T23:59');
    const [species, setSpecies] = useState('');
    const [subtype, setSubtype] = useState('H5N1');
    const [center, setCenter] = useState('Bern');

    const togglePopulation = (p: Population) => {
        setPopulation((prev) =>
            prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p],
        );
    };

    return (
        <DashboardLayout>
            <Head title="Impressum · TS-Scanner" />
            <LagebildHeader title="TS-Scanner" subtitle="Impressum" />
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
                <div className="flex flex-1 flex-col overflow-hidden">
                    <div className="relative flex-1 overflow-y-auto rounded-md border bg-card p-8">
                        <Link
                            href="/dashboard/map"
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
                                    Im Rahmen des GovTech Hackathon 2026 entwickeltes Projekt. Es handelt sich um einen Prototypen, der nicht für den produktiven Einsatz bestimmt ist. Alle Daten und Inhalte sind fiktiv und dienen ausschließlich Demonstrationszwecken.
                                </p>
                            </section>
                            
                            <section className="space-y-2">
                                <h2 className="text-base font-semibold">Challenge Owner</h2>
                                <p className="text-muted-foreground">
                                    Bundesamt für Lebensmittelsicherheit und Veterinärwesen BLV
                                </p>
                            </section>

                            <section className="space-y-2">
                                <h2 className="text-base font-semibold">Kontakt</h2>
                                <p className="text-muted-foreground">
                                    Bundesamt für Lebensmittelsicherheit und Veterinärwesen (BLV)
                                    <br />
                                    Schwarzenburgstrasse 155, 3003 Bern
                                    <br />
                                    <br />
                                    <a href="mailto:info@ts-scanner.ch" className="text-muted-foreground hover:underline">info@ts-scanner.ch</a>
                                </p>
                            </section>

                            <section className="space-y-2">
                                <h2 className="text-base font-semibold">Haftungsausschluss</h2>
                                <p className="text-muted-foreground">
                                    Trotz sorgfältiger inhaltlicher Kontrolle übernehmen wir keine Haftung für die Inhalte externer Links. Für den Inhalt der verlinkten Seiten sind ausschließlich deren Betreiber verantwortlich.
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
                                    <li>
                                        <a
                                            href="https://www.woah.org"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-primary hover:underline"
                                        >
                                            World Organisation for Animal Health (WOAH)
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

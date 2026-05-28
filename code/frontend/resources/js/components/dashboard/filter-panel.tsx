import { Link } from '@inertiajs/react';
import { Crosshair } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';

type Population = 'wild' | 'poultry' | 'captive';

type Props = {
    population: Population[];
    onTogglePopulation: (p: Population) => void;
    dateFrom: string;
    dateTo: string;
    onDateFromChange: (v: string) => void;
    onDateToChange: (v: string) => void;
    species: string;
    onSpeciesChange: (v: string) => void;
    subtype: string;
    onSubtypeChange: (v: string) => void;
    center: string;
    onCenterChange: (v: string) => void;
};

const POP_OPTIONS: { value: Population; label: string }[] = [
    { value: 'wild', label: 'Wild' },
    { value: 'poultry', label: 'Poultry' },
    { value: 'captive', label: 'Captive' },
];

export default function FilterPanel({
    population,
    onTogglePopulation,
    dateFrom,
    dateTo,
    onDateFromChange,
    onDateToChange,
    species,
    onSpeciesChange,
    subtype,
    onSubtypeChange,
    center,
    onCenterChange,
}: Props) {
    return (
        <aside className="flex h-full w-72 shrink-0 flex-col gap-5 overflow-y-auto rounded-md border bg-card p-4 text-sm">
            <div className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">
                Filter
            </div>

            <div className="space-y-1.5">
                <label className="text-xs font-medium">Tierseuche</label>
                <select
                    className="w-full rounded-md border bg-background px-2 py-1.5 text-sm"
                    value="HPAI"
                    disabled
                >
                    <option value="HPAI">HPAI · aviäre Influenza</option>
                </select>
            </div>

            <div className="space-y-1.5">
                <div className="flex items-baseline justify-between">
                    <label className="text-xs font-medium">Population</label>
                </div>
                <div className="flex flex-wrap gap-1.5">
                    {POP_OPTIONS.map((opt) => {
                        const active = population.includes(opt.value);
                        return (
                            <Badge
                                key={opt.value}
                                asChild
                                variant={active ? 'default' : 'outline'}
                            >
                                <button
                                    type="button"
                                    onClick={() => onTogglePopulation(opt.value)}
                                    className="cursor-pointer px-2.5"
                                >
                                    {opt.label}
                                </button>
                            </Badge>
                        );
                    })}
                </div>
            </div>

            <div className="space-y-1.5">
                <div className="flex items-baseline justify-between">
                    <label className="text-xs font-medium">Zeitraum</label>
                </div>
                <div className="space-y-2">
                    <Input
                        type="datetime-local"
                        value={dateFrom}
                        onChange={(e) => onDateFromChange(e.target.value)}
                    />
                    <Input
                        type="datetime-local"
                        value={dateTo}
                        onChange={(e) => onDateToChange(e.target.value)}
                    />
                </div>
            </div>

            <div className="space-y-1.5">
                <label className="text-xs font-medium">Spezies</label>
                <select
                    className="w-full rounded-md border bg-background px-2 py-1.5 text-sm"
                    value={species}
                    onChange={(e) => onSpeciesChange(e.target.value)}
                >
                    <option value="">Alle Spezies</option>
                    <option value="duck">Ente</option>
                    <option value="chicken">Huhn</option>
                    <option value="swan">Schwan</option>
                </select>
            </div>

            <div className="space-y-1.5">
                <label className="text-xs font-medium">Subtype</label>
                <select
                    className="w-full rounded-md border bg-background px-2 py-1.5 text-sm"
                    value={subtype}
                    onChange={(e) => onSubtypeChange(e.target.value)}
                >
                    <option value="H5N1">H5N1</option>
                    <option value="H5N8">H5N8</option>
                    <option value="H7N9">H7N9</option>
                </select>
            </div>

            <div className="space-y-1.5">
                <label className="flex items-center gap-1.5 text-xs font-medium">
                    <Crosshair className="size-3.5" />
                    Ausgangsort (Zentrum)
                </label>
                <select
                    className="w-full rounded-md border bg-background px-2 py-1.5 text-sm"
                    value={center}
                    onChange={(e) => onCenterChange(e.target.value)}
                >
                    <option value="Bern">Bern</option>
                    <option value="Zürich">Zürich</option>
                    <option value="Genf">Genf</option>
                    <option value="Basel">Basel</option>
                </select>
            </div>

            <div className="mt-auto space-y-2 border-t pt-3 text-[10px] text-muted-foreground">
                <div>
                    <div>Letztes Update</div>
                    <div>ADIS: 2026-05-12 · WAHIS: 2026-05-12</div>
                </div>
                <Link href="/imprint" className="text-primary hover:underline">
                    Impressum
                </Link>
            </div>
        </aside>
    );
}

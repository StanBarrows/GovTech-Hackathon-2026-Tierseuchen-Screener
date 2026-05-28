import { Link } from '@inertiajs/react';
import { CalendarIcon, Crosshair } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Input } from '@/components/ui/input';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { cn } from '@/lib/utils';

// "YYYY-MM-DDTHH:mm" <-> Date
function parseDateTimeLocal(value: string): Date | undefined {
    if (!value) return undefined;
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? undefined : d;
}

function formatDateTimeLocal(date: Date, time: string): string {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}T${time || '00:00'}`;
}

function getTimePart(value: string): string {
    return value?.includes('T') ? value.split('T')[1].slice(0, 5) : '00:00';
}

const DATE_FMT = new Intl.DateTimeFormat('de-CH', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
});

function DateTimePicker({
    value,
    onChange,
}: {
    value: string;
    onChange: (v: string) => void;
}) {
    const date = parseDateTimeLocal(value);
    const time = getTimePart(value);

    return (
        <div className="flex gap-2">
            <Popover>
                <PopoverTrigger asChild>
                    <Button
                        variant="outline"
                        className={cn(
                            'flex-1 justify-start px-2 font-normal',
                            !date && 'text-muted-foreground',
                        )}
                    >
                        <CalendarIcon className="mr-1.5 size-3.5" />
                        {date ? DATE_FMT.format(date) : 'Datum wählen'}
                    </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                        mode="single"
                        selected={date}
                        onSelect={(d) => {
                            if (d) onChange(formatDateTimeLocal(d, time));
                        }}
                        autoFocus
                    />
                </PopoverContent>
            </Popover>
            <Input
                type="time"
                value={time}
                onChange={(e) => {
                    if (date) onChange(formatDateTimeLocal(date, e.target.value));
                }}
                className="w-[6.5rem] shrink-0"
            />
        </div>
    );
}

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
    speciesOptions: string[];
    subtype: string;
    onSubtypeChange: (v: string) => void;
    center: string;
    onCenterChange: (v: string) => void;
    radiusKm: number;
    onRadiusChange: (v: number) => void;
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
    speciesOptions,
    subtype,
    onSubtypeChange,
    center,
    onCenterChange,
    radiusKm,
    onRadiusChange,
}: Props) {
    return (
        <aside className="flex w-full shrink-0 flex-col gap-5 rounded-md border bg-card p-4 text-sm md:h-full md:w-72 md:overflow-y-auto">
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
                    <DateTimePicker value={dateFrom} onChange={onDateFromChange} />
                    <DateTimePicker value={dateTo} onChange={onDateToChange} />
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
                    {speciesOptions.map((s) => (
                        <option key={s} value={s}>
                            {s}
                        </option>
                    ))}
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
                <div className="space-y-1 pt-2">
                    <div className="flex items-baseline justify-between">
                        <label className="text-xs font-medium">Reichweite</label>
                        <span className="text-[11px] text-muted-foreground tabular-nums">
                            {radiusKm} km
                        </span>
                    </div>
                    <input
                        type="range"
                        min={10}
                        max={200}
                        step={5}
                        value={radiusKm}
                        onChange={(e) => onRadiusChange(Number(e.target.value))}
                        className="w-full accent-primary"
                    />
                </div>
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

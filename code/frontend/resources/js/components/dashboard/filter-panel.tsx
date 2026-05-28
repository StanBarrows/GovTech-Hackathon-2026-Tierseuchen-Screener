import { Link } from '@inertiajs/react';
import { CalendarIcon, CheckIcon, ChevronsUpDownIcon, Crosshair } from 'lucide-react';
import { useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import {
    Command,
    CommandEmpty,
    CommandGroup,
    CommandInput,
    CommandItem,
    CommandList,
} from '@/components/ui/command';
import { Input } from '@/components/ui/input';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';

// "YYYY-MM-DDTHH:mm" <-> Date
function parseDateTimeLocal(value: string): Date | undefined {
    if (!value) {
return undefined;
}

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
                            if (d) {
onChange(formatDateTimeLocal(d, time));
}
                        }}
                        autoFocus
                    />
                </PopoverContent>
            </Popover>
            <Input
                type="time"
                step="60"
                value={time}
                onChange={(e) => {
                    if (date) {
onChange(formatDateTimeLocal(date, e.target.value));
}
                }}
                className="w-[6.5rem] shrink-0 bg-background appearance-none [&::-webkit-calendar-picker-indicator]:hidden [&::-webkit-calendar-picker-indicator]:appearance-none"
            />
        </div>
    );
}

type Population = 'wild' | 'poultry' | 'captive';

type Props = {
    population: Population[];
    onTogglePopulation: (p: Population) => void;
    onResetPopulation: () => void;
    populationOptions: Population[];
    dateFrom: string;
    dateTo: string;
    onDateFromChange: (v: string) => void;
    onDateToChange: (v: string) => void;
    species: string[];
    onToggleSpecies: (v: string) => void;
    onResetSpecies: () => void;
    speciesOptions: string[];
    subtype: string[];
    onToggleSubtype: (v: string) => void;
    onResetSubtype: () => void;
    subtypeOptions: string[];
    center: string;
    onCenterChange: (v: string) => void;
    radiusKm: number;
    onRadiusChange: (v: number) => void;
};

const POP_LABELS: Record<Population, string> = {
    wild: 'Wild',
    poultry: 'Poultry',
    captive: 'Captive',
};

const POP_FALLBACK: Population[] = ['wild', 'poultry', 'captive'];

export default function FilterPanel({
    population,
    onTogglePopulation,
    onResetPopulation,
    populationOptions,
    dateFrom,
    dateTo,
    onDateFromChange,
    onDateToChange,
    species,
    onToggleSpecies,
    onResetSpecies,
    speciesOptions,
    subtype,
    onToggleSubtype,
    onResetSubtype,
    subtypeOptions,
    center,
    onCenterChange,
    radiusKm,
    onRadiusChange,
}: Props) {
    const [speciesOpen, setSpeciesOpen] = useState(false);
    const [subtypeOpen, setSubtypeOpen] = useState(false);
    const popOptions = populationOptions.length > 0 ? populationOptions : POP_FALLBACK;

    return (
        <aside className="flex w-full shrink-0 flex-col gap-5 rounded-md border bg-card p-4 text-sm md:h-full md:w-72 md:overflow-y-auto">
            <div className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">
                Filter
            </div>

            <div className="space-y-1.5">
                <label className="text-xs font-medium">Tierseuche</label>
                <Select value="HPAI" disabled>
                    <SelectTrigger className="w-full">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="HPAI">HPAI · aviäre Influenza</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            <div className="space-y-1.5">
                <div className="flex items-baseline justify-between">
                    <label className="text-xs font-medium">Population</label>
                    {population.length > 0 && (
                        <button
                            type="button"
                            onClick={onResetPopulation}
                            className="text-[11px] text-primary hover:underline"
                        >
                            Zurücksetzen
                        </button>
                    )}
                </div>
                <Popover>
                    <PopoverTrigger asChild>
                        <Button
                            variant="outline"
                            role="combobox"
                            className="w-full justify-between px-2 font-normal"
                        >
                            <span className="flex flex-1 flex-wrap gap-1 text-left">
                                {population.length === 0 ? (
                                    <span className="text-muted-foreground">
                                        Alle Populationen
                                    </span>
                                ) : (
                                    population.map((p) => (
                                        <Badge
                                            key={p}
                                            variant="secondary"
                                            className="px-1.5 py-0 text-[10px]"
                                        >
                                            {POP_LABELS[p] ?? p}
                                        </Badge>
                                    ))
                                )}
                            </span>
                            <ChevronsUpDownIcon className="ml-1 size-3.5 shrink-0 opacity-50" />
                        </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-(--radix-popover-trigger-width) p-0" align="start">
                        <Command>
                            <CommandInput placeholder="Suchen…" />
                            <CommandList>
                                <CommandEmpty>Keine Treffer.</CommandEmpty>
                                <CommandGroup>
                                    {popOptions.map((value) => {
                                        const active = population.includes(value);
                                        const label = POP_LABELS[value] ?? value;

                                        return (
                                            <CommandItem
                                                key={value}
                                                value={label}
                                                onSelect={() => onTogglePopulation(value)}
                                            >
                                                <CheckIcon
                                                    className={cn(
                                                        'size-4',
                                                        active ? 'opacity-100' : 'opacity-0',
                                                    )}
                                                />
                                                {label}
                                            </CommandItem>
                                        );
                                    })}
                                </CommandGroup>
                            </CommandList>
                        </Command>
                    </PopoverContent>
                </Popover>
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
                <div className="flex items-baseline justify-between">
                    <label className="text-xs font-medium">Spezies</label>
                    {species.length > 0 && (
                        <button
                            type="button"
                            onClick={onResetSpecies}
                            className="text-[11px] text-primary hover:underline"
                        >
                            Zurücksetzen
                        </button>
                    )}
                </div>
                <Popover open={speciesOpen} onOpenChange={setSpeciesOpen}>
                    <PopoverTrigger asChild>
                        <Button
                            variant="outline"
                            role="combobox"
                            aria-expanded={speciesOpen}
                            className="w-full justify-between px-2 font-normal"
                        >
                            <span className="flex flex-1 flex-wrap gap-1 text-left">
                                {species.length === 0 ? (
                                    <span className="text-muted-foreground">
                                        Alle Spezies
                                    </span>
                                ) : (
                                    species.map((s) => (
                                        <Badge
                                            key={s}
                                            variant="secondary"
                                            className="px-1.5 py-0 text-[10px]"
                                        >
                                            {s}
                                        </Badge>
                                    ))
                                )}
                            </span>
                            <ChevronsUpDownIcon className="ml-1 size-3.5 shrink-0 opacity-50" />
                        </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-(--radix-popover-trigger-width) p-0" align="start">
                        <Command>
                            <CommandInput placeholder="Spezies suchen…" />
                            <CommandList>
                                <CommandEmpty>Keine Treffer.</CommandEmpty>
                                <CommandGroup>
                                    {speciesOptions.map((s) => {
                                        const active = species.includes(s);

                                        return (
                                            <CommandItem
                                                key={s}
                                                value={s}
                                                onSelect={() => onToggleSpecies(s)}
                                            >
                                                <CheckIcon
                                                    className={cn(
                                                        'size-4',
                                                        active ? 'opacity-100' : 'opacity-0',
                                                    )}
                                                />
                                                {s}
                                            </CommandItem>
                                        );
                                    })}
                                </CommandGroup>
                            </CommandList>
                        </Command>
                    </PopoverContent>
                </Popover>
            </div>

            <div className="space-y-1.5">
                <div className="flex items-baseline justify-between">
                    <label className="text-xs font-medium">Subtype</label>
                    {subtype.length > 0 && (
                        <button
                            type="button"
                            onClick={onResetSubtype}
                            className="text-[11px] text-primary hover:underline"
                        >
                            Zurücksetzen
                        </button>
                    )}
                </div>
                <Popover open={subtypeOpen} onOpenChange={setSubtypeOpen}>
                    <PopoverTrigger asChild>
                        <Button
                            variant="outline"
                            role="combobox"
                            aria-expanded={subtypeOpen}
                            className="w-full justify-between px-2 font-normal"
                        >
                            <span className="flex flex-1 flex-wrap gap-1 text-left">
                                {subtype.length === 0 ? (
                                    <span className="text-muted-foreground">
                                        Alle Subtypes
                                    </span>
                                ) : (
                                    subtype.map((s) => (
                                        <Badge
                                            key={s}
                                            variant="secondary"
                                            className="px-1.5 py-0 text-[10px]"
                                        >
                                            {s}
                                        </Badge>
                                    ))
                                )}
                            </span>
                            <ChevronsUpDownIcon className="ml-1 size-3.5 shrink-0 opacity-50" />
                        </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-(--radix-popover-trigger-width) p-0" align="start">
                        <Command>
                            <CommandInput placeholder="Subtype suchen…" />
                            <CommandList>
                                <CommandEmpty>Keine Treffer.</CommandEmpty>
                                <CommandGroup>
                                    {subtypeOptions.map((s) => {
                                        const active = subtype.includes(s);

                                        return (
                                            <CommandItem
                                                key={s}
                                                value={s}
                                                onSelect={() => onToggleSubtype(s)}
                                            >
                                                <CheckIcon
                                                    className={cn(
                                                        'size-4',
                                                        active ? 'opacity-100' : 'opacity-0',
                                                    )}
                                                />
                                                {s}
                                            </CommandItem>
                                        );
                                    })}
                                </CommandGroup>
                            </CommandList>
                        </Command>
                    </PopoverContent>
                </Popover>
            </div>

            <div className="space-y-1.5">
                <label className="flex items-center gap-1.5 text-xs font-medium">
                    <Crosshair className="size-3.5" />
                    Ausgangsort (Zentrum)
                </label>
                <Select value={center} onValueChange={onCenterChange}>
                    <SelectTrigger className="w-full">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="Bern">Bern</SelectItem>
                        <SelectItem value="Zürich">Zürich</SelectItem>
                        <SelectItem value="Genf">Genf</SelectItem>
                        <SelectItem value="Basel">Basel</SelectItem>
                    </SelectContent>
                </Select>
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

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
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
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

function DateRangePicker({
    from,
    to,
    onFromChange,
    onToChange,
}: {
    from: string;
    to: string;
    onFromChange: (v: string) => void;
    onToChange: (v: string) => void;
}) {
    const fromDate = parseDateTimeLocal(from);
    const toDate = parseDateTimeLocal(to);
    const fromTime = getTimePart(from);
    const toTime = getTimePart(to);

    const label = (() => {
        if (fromDate && toDate) {
            return `${DATE_FMT.format(fromDate)} – ${DATE_FMT.format(toDate)}`;
        }

        if (fromDate) {
            return `${DATE_FMT.format(fromDate)} – …`;
        }

        if (toDate) {
            return `… – ${DATE_FMT.format(toDate)}`;
        }

        return 'Zeitraum wählen';
    })();

    return (
        <Popover>
            <PopoverTrigger asChild>
                <Button
                    variant="outline"
                    className={cn(
                        'w-full justify-start px-2 font-normal',
                        !fromDate && !toDate && 'text-muted-foreground',
                    )}
                >
                    <CalendarIcon className="mr-1.5 size-3.5" />
                    {label}
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                    mode="range"
                    numberOfMonths={2}
                    defaultMonth={fromDate ?? toDate}
                    selected={{ from: fromDate, to: toDate }}
                    onSelect={(range) => {
                        if (range?.from) {
                            onFromChange(formatDateTimeLocal(range.from, fromTime));
                        } else {
                            onFromChange('');
                        }

                        if (range?.to) {
                            onToChange(formatDateTimeLocal(range.to, toTime || '23:59'));
                        } else {
                            onToChange('');
                        }
                    }}
                    autoFocus
                />
            </PopoverContent>
        </Popover>
    );
}

type Population = 'wild' | 'poultry' | 'captive';

type Props = {
    disease: string[];
    onToggleDisease: (v: string) => void;
    onResetDisease: () => void;
    diseaseOptions: string[];
    population: Population[];
    onTogglePopulation: (p: Population) => void;
    onResetPopulation: () => void;
    populationOptions: Population[];
    dateFrom: string;
    dateTo: string;
    onDateFromChange: (v: string) => void;
    onDateToChange: (v: string) => void;
    onResetDate: () => void;
    dateChanged: boolean;
    species: string[];
    onToggleSpecies: (v: string) => void;
    onResetSpecies: () => void;
    speciesOptions: string[];
    subtype: string[];
    onToggleSubtype: (v: string) => void;
    onResetSubtype: () => void;
    subtypeOptions: string[];
};

const POP_LABELS: Record<Population, string> = {
    wild: 'Wild',
    poultry: 'Poultry',
    captive: 'Captive',
};

const POP_FALLBACK: Population[] = ['wild', 'poultry', 'captive'];

export default function FilterPanel({
    disease,
    onToggleDisease,
    onResetDisease,
    diseaseOptions,
    population,
    onTogglePopulation,
    onResetPopulation,
    populationOptions,
    dateFrom,
    dateTo,
    onDateFromChange,
    onDateToChange,
    onResetDate,
    dateChanged,
    species,
    onToggleSpecies,
    onResetSpecies,
    speciesOptions,
    subtype,
    onToggleSubtype,
    onResetSubtype,
    subtypeOptions,
}: Props) {
    const [diseaseOpen, setDiseaseOpen] = useState(false);
    const [speciesOpen, setSpeciesOpen] = useState(false);
    const [subtypeOpen, setSubtypeOpen] = useState(false);
    const popOptions = populationOptions.length > 0 ? populationOptions : POP_FALLBACK;

    return (
        <aside className="flex w-full shrink-0 flex-col gap-5 rounded-md border bg-card p-4 text-sm md:h-full md:w-72 md:overflow-y-auto">
            <div className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">
                Filter
            </div>

            <div className="space-y-1.5">
                <div className="flex items-baseline justify-between">
                    <label className="text-xs font-medium">Tierseuche</label>
                    {disease.length > 0 && (
                        <button
                            type="button"
                            onClick={onResetDisease}
                            className="text-[11px] text-primary hover:underline"
                        >
                            Zurücksetzen
                        </button>
                    )}
                </div>
                <Popover open={diseaseOpen} onOpenChange={setDiseaseOpen}>
                    <PopoverTrigger asChild>
                        <Button
                            variant="outline"
                            role="combobox"
                            aria-expanded={diseaseOpen}
                            className="w-full justify-between px-2 font-normal"
                        >
                            <span className="flex flex-1 flex-wrap gap-1 text-left">
                                {disease.length === 0 ? (
                                    <span className="text-muted-foreground">
                                        Alle Tierseuchen
                                    </span>
                                ) : (
                                    disease.map((d) => (
                                        <Badge
                                            key={d}
                                            variant="secondary"
                                            className="px-1.5 py-0 text-[10px]"
                                        >
                                            {d}
                                        </Badge>
                                    ))
                                )}
                            </span>
                            <ChevronsUpDownIcon className="ml-1 size-3.5 shrink-0 opacity-50" />
                        </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-(--radix-popover-trigger-width) p-0" align="start">
                        <Command>
                            <CommandInput placeholder="Tierseuche suchen…" />
                            <CommandList>
                                <CommandEmpty>Keine Treffer.</CommandEmpty>
                                <CommandGroup>
                                    {diseaseOptions.map((d) => {
                                        const active = disease.includes(d);

                                        return (
                                            <CommandItem
                                                key={d}
                                                value={d}
                                                onSelect={() => onToggleDisease(d)}
                                            >
                                                <CheckIcon
                                                    className={cn(
                                                        'size-4',
                                                        active ? 'opacity-100' : 'opacity-0',
                                                    )}
                                                />
                                                {d}
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
                    {dateChanged && (
                        <button
                            type="button"
                            onClick={onResetDate}
                            className="text-[11px] text-primary hover:underline"
                        >
                            Zurücksetzen
                        </button>
                    )}
                </div>
                <DateRangePicker
                    from={dateFrom}
                    to={dateTo}
                    onFromChange={onDateFromChange}
                    onToChange={onDateToChange}
                />
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
                    Ausgangsort
                </label>
                <div className="text-sm text-muted-foreground">Bern, Switzerland</div>
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

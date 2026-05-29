import { Link } from '@inertiajs/react';
import { InfoIcon } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';

type Props = {
    title: string;
};

const LANGUAGES = [
    { value: 'de', label: 'DE' },
    { value: 'fr', label: 'FR' },
    { value: 'it', label: 'IT' },
    { value: 'en', label: 'EN' },
];

export default function LagebildHeader({ title }: Props) {
    const [language, setLanguage] = useState('de');

    return (
        <header className="flex items-center justify-between gap-6 border-b bg-card px-6 py-3">
            <div className="flex items-baseline gap-3">
                <h1 className="text-lg font-semibold">
                    <Link href="/">{title}</Link>
                </h1>
            </div>

            <div className="flex items-center gap-2">
                <Popover>
                    <PopoverTrigger asChild>
                        <Button
                            variant="ghost"
                            size="icon"
                            className="size-8"
                            aria-label="Hinweis zu den Daten"
                        >
                            <InfoIcon className="size-4" />
                        </Button>
                    </PopoverTrigger>
                    <PopoverContent align="end" className="text-sm">
                        Die hier angezeigten Daten sind <strong>Mockdaten</strong> und
                        dienen ausschliesslich Entwicklungszwecken.
                    </PopoverContent>
                </Popover>

                <Select value={language} onValueChange={setLanguage}>
                    <SelectTrigger size="sm" className="w-20" aria-label="Sprache wählen">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent align="end">
                        {LANGUAGES.map((lang) => (
                            <SelectItem
                                key={lang.value}
                                value={lang.value}
                                disabled={lang.value !== 'de'}
                            >
                                {lang.label}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>
        </header>
    );
}

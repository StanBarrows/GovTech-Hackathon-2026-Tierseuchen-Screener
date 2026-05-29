import { useState } from 'react';

import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';

type Props = {
    title: string;
    subtitle?: string;
};

const LANGUAGES = [
    { value: 'de', label: 'DE' },
    { value: 'fr', label: 'FR' },
    { value: 'it', label: 'IT' },
    { value: 'en', label: 'EN' },
];

export default function LagebildHeader({ title, subtitle }: Props) {
    const [language, setLanguage] = useState('de');

    return (
        <header className="flex items-center justify-between gap-6 border-b bg-card px-6 py-3">
            <div className="flex items-baseline gap-3">
                <h1 className="text-lg font-semibold">{title}</h1>
                {subtitle && (
                    <span className="text-xs text-muted-foreground">{subtitle}</span>
                )}
            </div>

            <Select value={language} onValueChange={setLanguage}>
                <SelectTrigger size="sm" className="w-20" aria-label="Sprache wählen">
                    <SelectValue />
                </SelectTrigger>
                <SelectContent align="end">
                    {LANGUAGES.map((lang) => (
                        <SelectItem key={lang.value} value={lang.value}>
                            {lang.label}
                        </SelectItem>
                    ))}
                </SelectContent>
            </Select>
        </header>
    );
}

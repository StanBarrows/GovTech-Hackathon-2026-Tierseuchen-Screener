import { Badge } from '@/components/ui/badge';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';

import type { Population } from '@/types/case';

type DetailCase = {
    id: number | string;
    disease: string;
    population?: Population;
    location: string;
    canton?: string;
    species?: string;
    subtype?: string;
    lat: number | null;
    lng: number | null;
    reportedAt: string;
    distance?: number;
    priority?: 'high' | 'medium' | 'low';
};

type Props = {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    item: DetailCase | null;
};

const PRIORITY_LABEL: Record<'high' | 'medium' | 'low', string> = {
    high: 'Hoch',
    medium: 'Mittel',
    low: 'Tief',
};

const PRIORITY_COLOR: Record<'high' | 'medium' | 'low', string> = {
    high: 'bg-red-500',
    medium: 'bg-amber-500',
    low: 'bg-emerald-500',
};

const POP_LABEL: Record<Population, string> = {
    wild: 'Wild',
    poultry: 'Poultry',
    captive: 'Captive',
};

function Row({ label, value }: { label: string; value: React.ReactNode }) {
    return (
        <div className="grid grid-cols-[110px_1fr] gap-3 border-b py-2 text-sm last:border-0">
            <div className="text-xs font-medium tracking-wider text-muted-foreground uppercase">
                {label}
            </div>
            <div>{value}</div>
        </div>
    );
}

function formatTimestamp(iso: string) {
    if (!iso) {
        return '—';
    }

    const [date, time] = iso.split('T');
    const [y, m, d] = date.split('-');

    return `${d}.${m}.${y} · ${time?.slice(0, 5) ?? ''} Uhr`;
}

export default function CaseDetailDialog({ open, onOpenChange, item }: Props) {
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-lg">
                {item && (
                    <>
                        <DialogHeader>
                            <DialogTitle className="flex items-center gap-2">
                                <Badge>{item.disease}</Badge>
                                <span>Meldung #{item.id}</span>
                            </DialogTitle>
                            <DialogDescription>
                                {item.location}
                                {item.canton ? ` (${item.canton})` : ''} ·{' '}
                                {formatTimestamp(item.reportedAt)}
                            </DialogDescription>
                        </DialogHeader>

                        <div className="mt-2">
                            {item.priority && (
                                <Row
                                    label="Priorität"
                                    value={
                                        <span className="inline-flex items-center gap-2">
                                            <span
                                                className={`inline-block size-2.5 rounded-full ${PRIORITY_COLOR[item.priority]}`}
                                            />
                                            {PRIORITY_LABEL[item.priority]}
                                        </span>
                                    }
                                />
                            )}
                            <Row label="Datum" value={formatTimestamp(item.reportedAt)} />
                            <Row
                                label="Region / Ort"
                                value={
                                    <>
                                        {item.location}
                                        {item.canton && (
                                            <span className="text-muted-foreground"> ({item.canton})</span>
                                        )}
                                    </>
                                }
                            />
                            <Row
                                label="Typ"
                                value={item.population ? POP_LABEL[item.population] : '—'}
                            />
                            <Row label="Spezies" value={item.species ?? '—'} />
                            <Row label="Subtype" value={item.subtype ?? '—'} />
                            <Row
                                label="Koordinaten"
                                value={
                                    item.lat != null && item.lng != null ? (
                                        <span className="tabular-nums">
                                            {item.lat.toFixed(4)}, {item.lng.toFixed(4)}
                                        </span>
                                    ) : (
                                        '—'
                                    )
                                }
                            />
                            {typeof item.distance === 'number' && (
                                <Row
                                    label="Distanz"
                                    value={
                                        <span className="tabular-nums">
                                            ~{Math.round(item.distance)} km zum Zentrum
                                        </span>
                                    }
                                />
                            )}
                        </div>
                    </>
                )}
            </DialogContent>
        </Dialog>
    );
}

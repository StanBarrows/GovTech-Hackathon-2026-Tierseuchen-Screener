import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

type Case = {
    id: number | string;
    disease: string;
    population?: 'wild' | 'poultry' | 'captive';
    location: string;
    reportedAt: string;
};

type Props = { cases: Case[] };

const POP_LABELS: Record<NonNullable<Case['population']>, string> = {
    wild: 'Wild',
    poultry: 'Poultry',
    captive: 'Captive',
};

export default function StatsSidebar({ cases }: Props) {
    const total = cases.length;
    const byPop = cases.reduce<Record<string, number>>((acc, c) => {
        if (c.population) acc[c.population] = (acc[c.population] ?? 0) + 1;
        return acc;
    }, {});
    const recent = [...cases]
        .sort((a, b) => (a.reportedAt < b.reportedAt ? 1 : -1))
        .slice(0, 6);

    return (
        <aside className="flex h-full w-80 shrink-0 flex-col gap-3 overflow-y-auto">
            <div className="grid grid-cols-2 gap-3">
                <Card>
                    <CardHeader>
                        <CardDescription>Meldungen</CardDescription>
                        <CardTitle className="text-2xl font-semibold">{total}</CardTitle>
                        <p className="text-xs text-muted-foreground">im Zeitraum</p>
                    </CardHeader>
                </Card>
                <Card>
                    <CardHeader>
                        <CardDescription>Risikostufe</CardDescription>
                        <CardTitle className="text-2xl font-semibold text-red-600">
                            {total > 6 ? 'Hoch' : total > 2 ? 'Mittel' : 'Tief'}
                        </CardTitle>
                        <p className="text-xs text-muted-foreground">aus Dichte abgeleitet</p>
                    </CardHeader>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle className="text-sm">Population</CardTitle>
                </CardHeader>
                <CardContent className="space-y-1.5 text-sm">
                    {(['wild', 'poultry', 'captive'] as const).map((p) => (
                        <div
                            key={p}
                            className="flex items-center justify-between border-b pb-1 last:border-0 last:pb-0"
                        >
                            <span>{POP_LABELS[p]}</span>
                            <span className="font-medium tabular-nums">{byPop[p] ?? 0}</span>
                        </div>
                    ))}
                    <div className="flex items-center justify-between pt-1.5 text-sm font-semibold">
                        <span>Total</span>
                        <span className="tabular-nums">{total}</span>
                    </div>
                </CardContent>
            </Card>

            <Card className="flex-1">
                <CardHeader>
                    <CardTitle className="text-sm">Aktuelle Meldungen</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                    {recent.length === 0 ? (
                        <p className="text-xs text-muted-foreground">Keine Meldungen.</p>
                    ) : (
                        recent.map((c) => (
                            <div key={c.id} className="flex items-center justify-between gap-2 border-b pb-2 last:border-0 last:pb-0">
                                <div className="min-w-0">
                                    <div className="flex items-center gap-1.5">
                                        <Badge variant="secondary">{c.disease}</Badge>
                                        {c.population && (
                                            <span className="text-[10px] text-muted-foreground uppercase">
                                                {c.population}
                                            </span>
                                        )}
                                    </div>
                                    <div className="truncate text-xs">{c.location}</div>
                                </div>
                                <div className="shrink-0 text-xs text-muted-foreground">
                                    {c.reportedAt}
                                </div>
                            </div>
                        ))
                    )}
                </CardContent>
            </Card>
        </aside>
    );
}

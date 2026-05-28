import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

type Stat = { label: string; value: string | number; hint?: string };

type Props = { stats: Stat[] };

export default function StatsCards({ stats }: Props) {
    return (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {stats.map((s) => (
                <Card key={s.label}>
                    <CardHeader>
                        <CardDescription>{s.label}</CardDescription>
                        <CardTitle className="text-2xl font-semibold">{s.value}</CardTitle>
                        {s.hint && <p className="text-xs text-muted-foreground">{s.hint}</p>}
                    </CardHeader>
                </Card>
            ))}
        </div>
    );
}

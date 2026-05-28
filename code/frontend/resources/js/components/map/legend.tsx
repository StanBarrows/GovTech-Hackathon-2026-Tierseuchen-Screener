import { Card } from '@/components/ui/card';
import { DISEASE_COLORS, DISEASE_LABELS  } from './disease-colors';
import type {DiseaseCode} from './disease-colors';

type Props = {
    diseases: DiseaseCode[];
    center?: string;
    radiusKm?: number;
};

const HEATMAP_STOPS: { color: string; label: string }[] = [
    { color: 'rgb(178,223,138)', label: 'gering' },
    { color: 'rgb(255,237,160)', label: '' },
    { color: 'rgb(254,178,76)', label: 'mittel' },
    { color: 'rgb(252,141,89)', label: '' },
    { color: 'rgb(215,48,39)', label: 'hoch' },
];

export default function Legend({ diseases, center, radiusKm }: Props) {
    const gradient = `linear-gradient(to right, ${HEATMAP_STOPS.map((s) => s.color).join(', ')})`;

    return (
        <Card className="absolute top-4 right-4 z-10 gap-2 px-3 py-2 text-xs shadow-sm">
            <div className="font-medium">Relevanz-Index</div>
            <div className="space-y-1">
                <div
                    aria-hidden
                    className="h-2 w-40 rounded-sm"
                    style={{ background: gradient }}
                />
                <div className="flex justify-between text-[10px] text-muted-foreground">
                    <span>gering</span>
                    <span>mittel</span>
                    <span>hoch</span>
                </div>
                {center && radiusKm != null && (
                    <div className="pt-0.5 text-[10px] text-muted-foreground">
                        bezogen auf {center} · Reichweite {radiusKm} km
                    </div>
                )}
            </div>

            <div className="mt-2 border-t pt-2">
                <div className="mb-1 font-medium">Seuchen</div>
                <ul className="space-y-1">
                    {diseases.map((d) => (
                        <li key={d} className="flex items-center gap-2">
                            <span
                                aria-hidden
                                className="inline-block size-2.5 rounded-full"
                                style={{ backgroundColor: DISEASE_COLORS[d] }}
                            />
                            <span className="text-foreground">{DISEASE_LABELS[d] ?? d}</span>
                        </li>
                    ))}
                </ul>
            </div>
        </Card>
    );
}

import { Card } from '@/components/ui/card';
import { DISEASE_COLORS, DISEASE_LABELS, type DiseaseCode } from './disease-colors';

type Props = { diseases: DiseaseCode[] };

export default function Legend({ diseases }: Props) {
    return (
        <Card className="absolute top-4 right-4 z-10 gap-2 px-3 py-2 text-xs shadow-sm">
            <div className="font-medium">Seuchen</div>
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
        </Card>
    );
}

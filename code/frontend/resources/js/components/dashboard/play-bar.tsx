import { FastForward, Pause, Play, RotateCcw } from 'lucide-react';
import { useEffect, useRef } from 'react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

type Props = {
    from: string;
    to: string;
    cursor: string;
    onCursorChange: (v: string) => void;
    playing: boolean;
    onTogglePlay: () => void;
    onReset: () => void;
    onSkipToEnd: () => void;
    stepHours?: number;
    tickMs?: number;
};

function toMs(v: string): number {
    return new Date(v).getTime();
}

function fromMs(ms: number): string {
    const d = new Date(ms);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function formatLabel(v: string): string {
    const d = new Date(v);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${String(d.getFullYear()).slice(2)} · ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export default function PlayBar({
    from,
    to,
    cursor,
    onCursorChange,
    playing,
    onTogglePlay,
    onReset,
    onSkipToEnd,
    stepHours = 6,
    tickMs = 120,
}: Props) {
    const fromMsVal = toMs(from);
    const toMsVal = toMs(to);
    const cursorMsVal = Math.min(Math.max(toMs(cursor), fromMsVal), toMsVal);

    const range = Math.max(toMsVal - fromMsVal, 1);
    const progress = ((cursorMsVal - fromMsVal) / range) * 100;

    const rafRef = useRef<number | null>(null);
    const lastTickRef = useRef<number>(0);

    useEffect(() => {
        if (!playing) return;

        const step = () => {
            const now = performance.now();
            if (now - lastTickRef.current >= tickMs) {
                lastTickRef.current = now;
                const next = cursorMsVal + stepHours * 60 * 60 * 1000;
                if (next >= toMsVal) {
                    onCursorChange(fromMs(toMsVal));
                    onTogglePlay();
                    return;
                }
                onCursorChange(fromMs(next));
            }
            rafRef.current = requestAnimationFrame(step);
        };
        rafRef.current = requestAnimationFrame(step);
        return () => {
            if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
        };
    }, [playing, cursorMsVal, toMsVal, stepHours, tickMs, onCursorChange, onTogglePlay]);

    const handleSlider = (e: React.ChangeEvent<HTMLInputElement>) => {
        const pct = Number(e.target.value) / 1000;
        onCursorChange(fromMs(fromMsVal + pct * range));
    };

    return (
        <Card className="flex flex-row items-center gap-3 px-4 py-3">
            <Button
                type="button"
                size="icon"
                variant={playing ? 'default' : 'outline'}
                onClick={onTogglePlay}
                aria-label={playing ? 'Pause' : 'Abspielen'}
            >
                {playing ? <Pause className="size-4" /> : <Play className="size-4" />}
            </Button>
            <Button
                type="button"
                size="icon"
                variant="outline"
                onClick={onReset}
                aria-label="Auf Anfang zurücksetzen"
                title="Auf Anfang zurücksetzen"
            >
                <RotateCcw className="size-4" />
            </Button>
            <Button
                type="button"
                size="icon"
                variant="outline"
                onClick={onSkipToEnd}
                aria-label="Zum Ende springen (alle Daten anzeigen)"
                title="Zum Ende springen (alle Daten)"
            >
                <FastForward className="size-4" />
            </Button>

            <div className="flex flex-1 flex-col gap-1">
                <input
                    type="range"
                    min={0}
                    max={1000}
                    value={Math.round((progress / 100) * 1000)}
                    onChange={handleSlider}
                    className="w-full accent-foreground"
                />
                <div className="flex justify-between text-[10px] text-muted-foreground tabular-nums">
                    <span>{formatLabel(from)}</span>
                    <span className="font-medium text-foreground">{formatLabel(fromMs(cursorMsVal))}</span>
                    <span>{formatLabel(to)}</span>
                </div>
            </div>
        </Card>
    );
}

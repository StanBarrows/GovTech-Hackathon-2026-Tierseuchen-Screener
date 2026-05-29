// Coordinated categorical palette for non-semantic chart series.
// Teal-led to align with the app's --primary brand color.
export const CHART_PALETTE = [
    '#0d9488', // teal   (brand-aligned)
    '#2563eb', // blue
    '#7c3aed', // violet
    '#d97706', // amber
    '#e11d48', // rose
    '#0891b2', // cyan
] as const;

// Pick a stable color by index (cycles for long series).
export function paletteColor(i: number): string {
    return CHART_PALETTE[i % CHART_PALETTE.length];
}

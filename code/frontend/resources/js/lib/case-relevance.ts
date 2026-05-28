export type Geo = { lat: number; lng: number };

export type Weighted = Geo & { weight?: number };

const EARTH_KM = 6371;

export function haversineKm(a: Geo, b: Geo): number {
    const toRad = (d: number) => (d * Math.PI) / 180;
    const dLat = toRad(b.lat - a.lat);
    const dLng = toRad(b.lng - a.lng);
    const lat1 = toRad(a.lat);
    const lat2 = toRad(b.lat);
    const h =
        Math.sin(dLat / 2) ** 2 +
        Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;

    return 2 * EARTH_KM * Math.asin(Math.sqrt(h));
}

export function decay(distanceKm: number, radiusKm: number): number {
    if (radiusKm <= 0) {
return 0;
}

    return Math.exp(-distanceKm / radiusKm);
}

export function relevance(c: Weighted, center: Geo | null, radiusKm: number): number {
    const w = c.weight ?? 1;

    if (!center) {
return w;
}

    return w * decay(haversineKm(c, center), radiusKm);
}

export function rankByRelevance<T extends Weighted>(
    cases: T[],
    center: Geo | null,
    radiusKm: number,
): { case: T; relevance: number }[] {
    return cases
        .map((c) => ({ case: c, relevance: relevance(c, center, radiusKm) }))
        .sort((a, b) => b.relevance - a.relevance);
}

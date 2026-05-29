import type { Case, RelevanceContext } from '@/types/case';

export type Geo = { lat: number; lng: number };

export type Weighted = Geo & { weight?: number };

const EPSILON = 1e-4;

export function contextMatches(
    centerLat: number,
    centerLng: number,
    radiusKm: number,
    ctx?: RelevanceContext | null,
): boolean {
    if (!ctx) {
        return false;
    }

    return (
        Math.abs(ctx.centerLat - centerLat) < EPSILON &&
        Math.abs(ctx.centerLng - centerLng) < EPSILON &&
        Math.abs(ctx.radiusKm - radiusKm) < EPSILON
    );
}

// The server computes distance and a relevance_score relative to the operational
// origin (Bern), so we prefer those values whenever present. The client-side
// recompute below is only a fallback for cases the server hasn't scored — there is
// no interactive re-centering in the UI, so the request-time context always holds.
export function resolveDistanceKm(
    c: Case,
    center: Geo,
    radiusKm: number,
    ctx?: RelevanceContext | null,
): number {
    if (c.distanceKm != null) {
        return c.distanceKm;
    }

    if (c.latitude == null || c.longitude == null) {
        return 0;
    }

    return haversineKm({ lat: c.latitude, lng: c.longitude }, center);
}

export function resolveRelevance(
    c: Case,
    center: Geo,
    radiusKm: number,
    ctx?: RelevanceContext | null,
): number {
    if (c.relevanceIndex != null) {
        return c.relevanceIndex;
    }

    if (c.latitude == null || c.longitude == null) {
        return 1;
    }

    return relevance({ lat: c.latitude, lng: c.longitude }, center, radiusKm);
}

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

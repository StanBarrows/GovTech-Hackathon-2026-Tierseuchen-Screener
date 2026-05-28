export type Population = 'wild' | 'poultry' | 'captive';

// Shape mirrors App\EventDto\EventDto::toArray().
// Field names follow Lindas OutbreakEvent.
export type Case = {
    iri: string;
    referenceId?: string | null;
    nationalReferenceId?: string | null;
    confirmationDate?: string | null;
    suspicionStartDate?: string | null;
    situationIri?: string | null;
    disease?: string | null;
    diseaseLabel?: string | null;
    subtype?: string | null;
    subtypeLabel?: string | null;
    species?: string | null;
    speciesLabel?: string | null;
    countryLabel?: string | null;
    admin1?: string | null;
    admin2?: string | null;
    admin3?: string | null;
    latitude?: number | null;
    longitude?: number | null;
    population?: Population | null;
    source?: string | null;
    distanceKm?: number | null;
    radiusKm?: number | null;
    relevanceIndex?: number | null;
};

export type RelevanceContext = {
    centerLat: number;
    centerLng: number;
    radiusKm: number;
};

export type Pagination = {
    page: number;
    perPage: number;
    total: number;
};

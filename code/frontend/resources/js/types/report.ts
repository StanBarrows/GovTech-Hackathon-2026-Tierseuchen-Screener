// Shape mirrors App\Http\Resources\ReportResource::toArray().
export type Report = {
    id: number;
    source?: string | null;
    title: string;
    url?: string | null;
    teaser?: string | null;
    body?: string | null;
    reportDate?: string | null;
    admin1?: string | null;
    admin2?: string | null;
    admin3?: string | null;
    relevanceScore?: number | null;
    relevanceLabel?: string | null;
};

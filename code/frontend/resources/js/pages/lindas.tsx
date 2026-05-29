import { Link, router } from '@inertiajs/react';
import { ArrowLeft, Database } from 'lucide-react';
import type { ReactNode } from 'react';

import { PageHead } from '@/components/seo/page-head';
import DashboardLayout from '@/layouts/dashboard-layout';
import type { SeoMeta } from '@/types/seo';

type EntityCounts = {
    outbreakEvents: number;
    outbreakSituations: number;
    paffReports: number;
    paffSituationStatements: number;
    evidenceSnippets: number;
};

type Meta = {
    endpoint: string;
    graphUri: string;
    tab: string;
    page: number;
    perPage: number;
    cacheEnabled?: boolean;
    cacheTtl?: number;
    demoEventIri?: string;
    demoReportIri?: string;
    demoSituationIri?: string;
    demoStatementIri?: string;
};

type OutbreakEventRow = {
    iri: string;
    referenceId?: string | null;
    nationalReferenceId?: string | null;
    confirmationDate?: string | null;
    suspicionStartDate?: string | null;
    situationIri?: string | null;
    diseaseLabel?: string | null;
    subtypeLabel?: string | null;
    speciesLabel?: string | null;
    countryLabel?: string | null;
    admin1?: string | null;
    admin2?: string | null;
    admin3?: string | null;
    latitude?: number | null;
    longitude?: number | null;
};

type SituationRow = {
    iri: string;
    key?: string | null;
    diseaseLabel?: string | null;
    countryLabel?: string | null;
    month?: string | null;
    eventCount: number;
};

type PaffLinkageRow = {
    eventIri: string;
    situationIri?: string | null;
    statementIri?: string | null;
    reportIri?: string | null;
    snippetIri?: string | null;
    relevanceLabel?: string | null;
    severityLabel?: string | null;
    reachLabel?: string | null;
    prevention?: string | null;
};

type SituationDetailRow = {
    situationKey?: string | null;
    situationMonth?: string | null;
    situationDiseaseLabel?: string | null;
    situationCountryLabel?: string | null;
    statementIri?: string | null;
    reportIri?: string | null;
    snippetText?: string | null;
    extractionStatusLabel?: string | null;
    extractionConfidenceLabel?: string | null;
    relevanceLevelLabel?: string | null;
    severityLevelLabel?: string | null;
    reachLevelLabel?: string | null;
    preventionText?: string | null;
    eventCount: number;
    events: OutbreakEventRow[];
};

type Snapshot = {
    meta: Meta;
    counts: EntityCounts;
    data: OutbreakEventRow[] | SituationRow[] | PaffLinkageRow | SituationDetailRow | null;
};

type Props = {
    snapshot: Snapshot;
    error: string | null;
    seo: SeoMeta;
};

const TABS = [
    { id: 'events', label: 'Events' },
    { id: 'situations', label: 'Situations' },
    { id: 'paff', label: 'PAFF Linkage' },
    { id: 'detail', label: 'Situation Detail' },
] as const;

function CountCard({ label, value }: { label: string; value: number }) {
    return (
        <div className="rounded-md border bg-card px-4 py-3">
            <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
            <div className="mt-1 text-2xl font-semibold tabular-nums">{value.toLocaleString()}</div>
        </div>
    );
}

function TableShell({ children }: { children: ReactNode }) {
    return (
        <div className="overflow-auto rounded-md border">
            <table className="min-w-full text-sm">{children}</table>
        </div>
    );
}

function Th({ children }: { children: ReactNode }) {
    return (
        <th className="sticky top-0 border-b bg-muted/80 px-3 py-2 text-left font-medium backdrop-blur">
            {children}
        </th>
    );
}

function Td({ children, mono = false }: { children: ReactNode; mono?: boolean }) {
    return (
        <td className={`border-b px-3 py-2 align-top ${mono ? 'font-mono text-xs break-all' : ''}`}>
            {children}
        </td>
    );
}

function tabHref(tab: string, page = 1) {
    const params = new URLSearchParams({ tab });

    if (tab === 'events' && page > 1) {
        params.set('page', String(page));
    }

    return `/lindas?${params.toString()}`;
}

export default function Lindas({ snapshot, error, seo }: Props) {
    const { meta, counts, data } = snapshot;
    const activeTab = meta.tab;

    return (
        <DashboardLayout>
            <PageHead seo={seo} />

            <header className="border-b bg-card px-4 py-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                        <Database className="size-5 text-muted-foreground" />
                        <div>
                            <h1 className="text-lg font-semibold">LINDAS Data Validator</h1>
                            <p className="text-xs text-muted-foreground">
                                Read-only SPARQL data from the govtech26 tierseuchen graph
                            </p>
                        </div>
                    </div>
                    <Link
                        href="/dashboard/map"
                        className="inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm hover:bg-muted"
                    >
                        <ArrowLeft className="size-3.5" />
                        Back to dashboard
                    </Link>
                </div>
            </header>

            <div className="flex flex-1 flex-col gap-4 overflow-hidden p-4">
                {error && (
                    <div className="rounded-md border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                        <strong>SPARQL error:</strong> {error}
                    </div>
                )}

                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                    <CountCard label="Outbreak Events" value={counts.outbreakEvents} />
                    <CountCard label="Situations" value={counts.outbreakSituations} />
                    <CountCard label="PAFF Reports" value={counts.paffReports} />
                    <CountCard label="PAFF Statements" value={counts.paffSituationStatements} />
                    <CountCard label="Evidence Snippets" value={counts.evidenceSnippets} />
                </div>

                <div className="rounded-md border bg-muted/30 px-4 py-3 text-xs text-muted-foreground">
                    <div>
                        <span className="font-medium text-foreground">Endpoint:</span>{' '}
                        <span className="font-mono">{meta.endpoint}</span>
                    </div>
                    <div className="mt-1">
                        <span className="font-medium text-foreground">Graph:</span>{' '}
                        <span className="font-mono">{meta.graphUri}</span>
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-3">
                        <span>
                            <span className="font-medium text-foreground">Cache:</span>{' '}
                            {meta.cacheEnabled
                                ? `enabled (${meta.cacheTtl ?? 0}s TTL)`
                                : 'disabled'}
                        </span>
                        {meta.cacheEnabled && (
                            <button
                                type="button"
                                onClick={() =>
                                    router.post('/lindas/cache/clear', {
                                        tab: meta.tab,
                                        page: meta.page,
                                        perPage: meta.perPage,
                                    })
                                }
                                className="rounded border px-2 py-0.5 text-foreground hover:bg-muted"
                            >
                                Clear cache
                            </button>
                        )}
                    </div>
                </div>

                <div className="inline-flex w-fit rounded-md border bg-card p-0.5 text-sm">
                    {TABS.map((tab) => (
                        <Link
                            key={tab.id}
                            href={tabHref(tab.id)}
                            className={`rounded px-3 py-1 ${
                                activeTab === tab.id
                                    ? 'bg-foreground text-background'
                                    : 'text-muted-foreground hover:bg-muted'
                            }`}
                        >
                            {tab.label}
                        </Link>
                    ))}
                </div>

                <div className="min-h-0 flex-1 overflow-auto">
                    {activeTab === 'events' && Array.isArray(data) && (
                        <>
                            <TableShell>
                                <thead>
                                    <tr>
                                        <Th>Reference</Th>
                                        <Th>Date</Th>
                                        <Th>Disease</Th>
                                        <Th>Subtype</Th>
                                        <Th>Species</Th>
                                        <Th>Country</Th>
                                        <Th>Admin</Th>
                                        <Th>Coords</Th>
                                        <Th>IRI</Th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {(data as OutbreakEventRow[]).map((row) => (
                                        <tr key={row.iri} className="hover:bg-muted/40">
                                            <Td>{row.referenceId ?? '—'}</Td>
                                            <Td>{row.confirmationDate ?? '—'}</Td>
                                            <Td>{row.diseaseLabel ?? '—'}</Td>
                                            <Td>{row.subtypeLabel ?? '—'}</Td>
                                            <Td>{row.speciesLabel ?? '—'}</Td>
                                            <Td>{row.countryLabel ?? '—'}</Td>
                                            <Td>
                                                {[row.admin1, row.admin2, row.admin3]
                                                    .filter(Boolean)
                                                    .join(' / ') || '—'}
                                            </Td>
                                            <Td>
                                                {row.latitude != null && row.longitude != null
                                                    ? `${row.latitude}, ${row.longitude}`
                                                    : '—'}
                                            </Td>
                                            <Td mono>{row.iri}</Td>
                                        </tr>
                                    ))}
                                </tbody>
                            </TableShell>

                            <div className="mt-3 flex items-center gap-2 text-sm">
                                <Link
                                    href={tabHref('events', Math.max(1, meta.page - 1))}
                                    className={`rounded-md border px-3 py-1 ${meta.page <= 1 ? 'pointer-events-none opacity-40' : 'hover:bg-muted'}`}
                                >
                                    Previous
                                </Link>
                                <span className="text-muted-foreground">
                                    Page {meta.page} · {meta.perPage} rows
                                </span>
                                <Link
                                    href={tabHref('events', meta.page + 1)}
                                    className="rounded-md border px-3 py-1 hover:bg-muted"
                                >
                                    Next
                                </Link>
                            </div>
                        </>
                    )}

                    {activeTab === 'situations' && Array.isArray(data) && (
                        <TableShell>
                            <thead>
                                <tr>
                                    <Th>Key</Th>
                                    <Th>Month</Th>
                                    <Th>Disease</Th>
                                    <Th>Country</Th>
                                    <Th>Events</Th>
                                    <Th>IRI</Th>
                                </tr>
                            </thead>
                            <tbody>
                                {(data as SituationRow[]).map((row) => (
                                    <tr key={row.iri} className="hover:bg-muted/40">
                                        <Td mono>{row.key ?? '—'}</Td>
                                        <Td>{row.month ?? '—'}</Td>
                                        <Td>{row.diseaseLabel ?? '—'}</Td>
                                        <Td>{row.countryLabel ?? '—'}</Td>
                                        <Td>{row.eventCount}</Td>
                                        <Td mono>{row.iri}</Td>
                                    </tr>
                                ))}
                            </tbody>
                        </TableShell>
                    )}

                    {activeTab === 'paff' && data && !Array.isArray(data) && (
                        <div className="space-y-4">
                            <div className="rounded-md border bg-card p-4 text-sm">
                                <div className="mb-2 text-xs text-muted-foreground">
                                    Demo event IRI
                                </div>
                                <div className="font-mono text-xs break-all">
                                    {meta.demoEventIri}
                                </div>
                            </div>
                            <TableShell>
                                <tbody>
                                    {Object.entries(data as PaffLinkageRow).map(([key, value]) => (
                                        <tr key={key} className="hover:bg-muted/40">
                                            <Th>{key}</Th>
                                            <Td mono>{value ?? '—'}</Td>
                                        </tr>
                                    ))}
                                </tbody>
                            </TableShell>
                        </div>
                    )}

                    {activeTab === 'detail' && data && !Array.isArray(data) && (
                        <div className="space-y-4">
                            <div className="grid gap-3 md:grid-cols-2">
                                {[
                                    ['Situation key', (data as SituationDetailRow).situationKey],
                                    ['Month', (data as SituationDetailRow).situationMonth],
                                    ['Disease', (data as SituationDetailRow).situationDiseaseLabel],
                                    ['Country', (data as SituationDetailRow).situationCountryLabel],
                                    ['Relevance', (data as SituationDetailRow).relevanceLevelLabel],
                                    ['Severity', (data as SituationDetailRow).severityLevelLabel],
                                    ['Reach', (data as SituationDetailRow).reachLevelLabel],
                                    ['Events in situation', (data as SituationDetailRow).eventCount],
                                ].map(([label, value]) => (
                                    <div key={String(label)} className="rounded-md border bg-card px-4 py-3 text-sm">
                                        <div className="text-xs text-muted-foreground">{label}</div>
                                        <div className="mt-1 break-words">{value ?? '—'}</div>
                                    </div>
                                ))}
                            </div>

                            {(data as SituationDetailRow).snippetText && (
                                <div className="rounded-md border bg-card p-4 text-sm">
                                    <div className="mb-2 text-xs text-muted-foreground">Snippet</div>
                                    <p className="whitespace-pre-wrap">
                                        {(data as SituationDetailRow).snippetText}
                                    </p>
                                </div>
                            )}

                            <TableShell>
                                <thead>
                                    <tr>
                                        <Th>Reference</Th>
                                        <Th>Date</Th>
                                        <Th>Species</Th>
                                        <Th>Admin</Th>
                                        <Th>Coords</Th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {(data as SituationDetailRow).events.map((row) => (
                                        <tr key={row.iri} className="hover:bg-muted/40">
                                            <Td>{row.referenceId ?? '—'}</Td>
                                            <Td>{row.confirmationDate ?? '—'}</Td>
                                            <Td>{row.speciesLabel ?? '—'}</Td>
                                            <Td>
                                                {[row.admin1, row.admin2, row.admin3]
                                                    .filter(Boolean)
                                                    .join(' / ') || '—'}
                                            </Td>
                                            <Td>
                                                {row.latitude != null && row.longitude != null
                                                    ? `${row.latitude}, ${row.longitude}`
                                                    : '—'}
                                            </Td>
                                        </tr>
                                    ))}
                                </tbody>
                            </TableShell>
                        </div>
                    )}
                </div>
            </div>
        </DashboardLayout>
    );
}

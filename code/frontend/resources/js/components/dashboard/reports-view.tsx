import { useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import type { Report } from '@/types/report';

type Props = {
    reports: Report[];
};

function relevanceVariant(label?: string | null) {
    switch (label?.toLowerCase()) {
        case 'high':
            return 'destructive' as const;
        case 'medium':
            return 'secondary' as const;
        default:
            return 'outline' as const;
    }
}

function formatRegion(report: Report): string {
    return [report.admin1, report.admin2].filter(Boolean).join(', ') || '–';
}

export default function ReportsView({ reports }: Props) {
    const [activeReport, setActiveReport] = useState<Report | null>(null);

    if (reports.length === 0) {
        return (
            <div className="flex min-h-[40vh] items-center justify-center rounded-md border bg-muted/30 p-4 text-sm text-muted-foreground">
                Keine Berichte im gewählten Zeitraum.
            </div>
        );
    }

    return (
        <>
            <div className="max-h-[calc(100vh-12rem)] overflow-auto rounded-md border">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="w-[1%] whitespace-nowrap">Datum</TableHead>
                            <TableHead>Quelle</TableHead>
                            <TableHead>Titel</TableHead>
                            <TableHead>Region</TableHead>
                            <TableHead>Relevanz</TableHead>
                            <TableHead className="w-[1%] text-right">Aktion</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {reports.map((r) => (
                            <TableRow key={r.id}>
                                <TableCell className="whitespace-nowrap tabular-nums">
                                    {r.reportDate ?? '–'}
                                </TableCell>
                                <TableCell className="text-muted-foreground">
                                    {r.source ?? '–'}
                                </TableCell>
                                <TableCell className="max-w-md truncate" title={r.title}>
                                    {r.title}
                                </TableCell>
                                <TableCell>{formatRegion(r)}</TableCell>
                                <TableCell>
                                    {r.relevanceLabel ? (
                                        <Badge variant={relevanceVariant(r.relevanceLabel)}>
                                            {r.relevanceLabel}
                                        </Badge>
                                    ) : (
                                        '–'
                                    )}
                                </TableCell>
                                <TableCell className="text-right">
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => setActiveReport(r)}
                                    >
                                        Details
                                    </Button>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </div>

            <Dialog
                open={activeReport !== null}
                onOpenChange={(open) => {
                    if (!open) {
setActiveReport(null);
}
                }}
            >
                <DialogContent className="sm:max-w-4xl">
                    {activeReport && (
                        <>
                            <DialogHeader>
                                <DialogTitle>{activeReport.title}</DialogTitle>
                                <DialogDescription>
                                    Berichtsdatum: {activeReport.reportDate ?? '–'}
                                    {activeReport.source ? ` · Quelle: ${activeReport.source}` : ''}
                                    {formatRegion(activeReport) !== '–'
                                        ? ` · Region: ${formatRegion(activeReport)}`
                                        : ''}
                                </DialogDescription>
                            </DialogHeader>

                            <div className="mt-2 max-h-[70vh] space-y-4 overflow-auto">
                                {activeReport.teaser && (
                                    <p className="text-sm font-medium text-foreground">
                                        {activeReport.teaser}
                                    </p>
                                )}
                                {activeReport.body && (
                                    <p className="text-sm whitespace-pre-wrap text-muted-foreground">
                                        {activeReport.body}
                                    </p>
                                )}
                                {activeReport.url && (
                                    <a
                                        href={activeReport.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-block text-sm font-medium text-primary underline-offset-4 hover:underline"
                                    >
                                        Quelle öffnen ↗
                                    </a>
                                )}
                            </div>
                        </>
                    )}
                </DialogContent>
            </Dialog>
        </>
    );
}

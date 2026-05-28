import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';

type Case = {
    id: number | string;
    disease: string;
    location: string;
    reportedAt: string;
};

type Props = { cases: Case[] };

export default function RecentCases({ cases }: Props) {
    return (
        <Card>
            <CardHeader>
                <CardTitle>Aktuelle Meldungen</CardTitle>
            </CardHeader>
            <CardContent className="px-0">
                {cases.length === 0 ? (
                    <p className="px-4 py-6 text-center text-sm text-muted-foreground">Keine Meldungen.</p>
                ) : (
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Seuche</TableHead>
                                <TableHead>Ort</TableHead>
                                <TableHead className="text-right">Gemeldet</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {cases.map((c) => (
                                <TableRow key={c.id}>
                                    <TableCell>
                                        <Badge variant="secondary">{c.disease}</Badge>
                                    </TableCell>
                                    <TableCell>{c.location}</TableCell>
                                    <TableCell className="text-right text-muted-foreground">
                                        {c.reportedAt}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                )}
            </CardContent>
        </Card>
    );
}

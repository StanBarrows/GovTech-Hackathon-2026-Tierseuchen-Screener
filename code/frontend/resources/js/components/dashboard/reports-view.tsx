import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';

type Report = {
    id: string;
    title: string;
    date: string;
};

const PLACEHOLDER_REPORTS: Report[] = [
    { id: 'R-001', title: 'Wochenbericht HPAI', date: '2026-05-26' },
    { id: 'R-002', title: 'Lagebericht ASP Grenzregion', date: '2026-05-19' },
    { id: 'R-003', title: 'Monatsbericht Mai', date: '2026-05-01' },
    { id: 'R-004', title: 'Sonderbericht Geflügel', date: '2026-04-22' },
];

export default function ReportsView() {
    return (
        <div className="rounded-md border">
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>ID</TableHead>
                        <TableHead>Titel</TableHead>
                        <TableHead>Datum</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {PLACEHOLDER_REPORTS.map((r) => (
                        <TableRow key={r.id}>
                            <TableCell className="font-mono text-xs">{r.id}</TableCell>
                            <TableCell>{r.title}</TableCell>
                            <TableCell>{r.date}</TableCell>
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
    );
}

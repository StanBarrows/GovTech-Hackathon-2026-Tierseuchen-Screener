export type DiseaseCode = 'HPAI' | 'MKS' | 'ASP' | 'BVD' | 'BT';

export const DISEASE_LABELS: Record<DiseaseCode, string> = {
    HPAI: 'Geflügelpest (HPAI)',
    MKS: 'Maul- und Klauenseuche',
    ASP: 'Afrikanische Schweinepest',
    BVD: 'Bovine Virusdiarrhoe',
    BT: 'Blauzungenkrankheit',
};

export const DISEASE_COLORS: Record<DiseaseCode, string> = {
    HPAI: '#dc2626',
    MKS: '#f59e0b',
    ASP: '#7c3aed',
    BVD: '#0ea5e9',
    BT: '#10b981',
};

export const DISEASE_FALLBACK = '#71717a';

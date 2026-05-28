import mapboxgl from 'mapbox-gl';
import { useEffect, useMemo, useRef } from 'react';

import 'mapbox-gl/dist/mapbox-gl.css';

import { DISEASE_COLORS, DISEASE_FALLBACK, type DiseaseCode } from './disease-colors';

export type Case = {
    id: number | string;
    disease: string;
    location: string;
    lat: number;
    lng: number;
    reportedAt: string;
};

type Props = { cases: Case[]; centerLat?: number; centerLng?: number };

const TOKEN = import.meta.env.VITE_MAPBOX_TOKEN as string | undefined;

const CH_CENTER: [number, number] = [8.23, 46.82];
const CH_ZOOM = 7;

const MAP_STYLE = 'mapbox://styles/mapbox/dark-v11';

function casesToFeatureCollection(cases: Case[]): GeoJSON.FeatureCollection<GeoJSON.Point> {
    return {
        type: 'FeatureCollection',
        features: cases.map((c) => ({
            type: 'Feature',
            geometry: { type: 'Point', coordinates: [c.lng, c.lat] },
            properties: {
                id: c.id,
                disease: c.disease,
                location: c.location,
                reportedAt: c.reportedAt,
            },
        })),
    };
}

function colorMatchExpression(): mapboxgl.ExpressionSpecification {
    const stops: (string | mapboxgl.ExpressionSpecification)[] = [];
    (Object.entries(DISEASE_COLORS) as [DiseaseCode, string][]).forEach(([code, color]) => {
        stops.push(code, color);
    });
    return ['match', ['get', 'disease'], ...stops, DISEASE_FALLBACK] as mapboxgl.ExpressionSpecification;
}

export default function CaseMap({ cases, centerLat, centerLng }: Props) {
    const containerRef = useRef<HTMLDivElement>(null);
    const mapRef = useRef<mapboxgl.Map | null>(null);

    const data = useMemo(() => casesToFeatureCollection(cases), [cases]);

    useEffect(() => {
        if (!containerRef.current || mapRef.current) return;

        if (TOKEN) {
            mapboxgl.accessToken = TOKEN;
        }

        const map = new mapboxgl.Map({
            container: containerRef.current,
            style: MAP_STYLE,
            center: CH_CENTER,
            zoom: CH_ZOOM,
            attributionControl: true,
        });
        mapRef.current = map;

        map.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'top-left');

        map.on('load', () => {
            map.addSource('cases', {
                type: 'geojson',
                data,
            });

            map.addLayer({
                id: 'cases-heatmap',
                type: 'heatmap',
                source: 'cases',
                maxzoom: 15,
                paint: {
                    'heatmap-weight': 1,
                    'heatmap-intensity': [
                        'interpolate', ['linear'], ['zoom'],
                        0, 1,
                        15, 3,
                    ],
                    'heatmap-color': [
                        'interpolate', ['linear'], ['heatmap-density'],
                        0, 'rgba(33,102,172,0)',
                        0.2, 'rgb(178,223,138)',
                        0.4, 'rgb(255,237,160)',
                        0.6, 'rgb(254,178,76)',
                        0.8, 'rgb(252,141,89)',
                        1, 'rgb(215,48,39)',
                    ],
                    'heatmap-radius': [
                        'interpolate', ['linear'], ['zoom'],
                        0, 8,
                        9, 30,
                        15, 60,
                    ],
                    'heatmap-opacity': [
                        'interpolate', ['linear'], ['zoom'],
                        7, 0.85,
                        15, 0.6,
                    ],
                },
            });

            map.addLayer({
                id: 'cases-points',
                type: 'circle',
                source: 'cases',
                minzoom: 10,
                paint: {
                    'circle-color': colorMatchExpression(),
                    'circle-radius': [
                        'interpolate', ['linear'], ['zoom'],
                        10, 4,
                        15, 8,
                    ],
                    'circle-stroke-color': '#ffffff',
                    'circle-stroke-width': 1.5,
                    'circle-opacity': [
                        'interpolate', ['linear'], ['zoom'],
                        9, 0,
                        11, 1,
                    ],
                },
            });

            map.on('click', 'cases-points', (e) => {
                const feature = e.features?.[0];
                if (!feature) return;
                const props = feature.properties ?? {};
                const coords = (feature.geometry as GeoJSON.Point).coordinates.slice() as [number, number];
                const color = DISEASE_COLORS[props.disease as DiseaseCode] ?? DISEASE_FALLBACK;

                new mapboxgl.Popup({ offset: 12, closeButton: true })
                    .setLngLat(coords)
                    .setHTML(
                        `<div style="font-family: inherit; font-size: 12px; line-height: 1.4;">
                            <div style="display:flex; align-items:center; gap:6px; font-weight:600;">
                                <span style="display:inline-block;width:8px;height:8px;border-radius:9999px;background:${color}"></span>
                                ${props.disease}
                            </div>
                            <div style="margin-top:4px;">${props.location}</div>
                            <div style="color:#71717a;">${props.reportedAt}</div>
                        </div>`,
                    )
                    .addTo(map);
            });

            const setPointerCursor = () => (map.getCanvas().style.cursor = 'pointer');
            const clearCursor = () => (map.getCanvas().style.cursor = '');
            map.on('mouseenter', 'cases-points', setPointerCursor);
            map.on('mouseleave', 'cases-points', clearCursor);
        });

        return () => {
            map.remove();
            mapRef.current = null;
        };
    }, []);

    useEffect(() => {
        const map = mapRef.current;
        if (!map) return;
        const apply = () => {
            const src = map.getSource('cases') as mapboxgl.GeoJSONSource | undefined;
            src?.setData(data);
        };
        if (map.isStyleLoaded()) apply();
        else map.once('load', apply);
    }, [data]);

    if (!TOKEN) {
        return (
            <div className="flex h-full items-center justify-center rounded-md border border-dashed bg-muted/30 p-6 text-center text-sm text-muted-foreground">
                <div>
                    <p className="font-medium text-foreground">Mapbox-Token fehlt</p>
                    <p className="mt-1">
                        Setze <code className="rounded bg-muted px-1">VITE_MAPBOX_TOKEN</code> in <code className="rounded bg-muted px-1">.env</code> und starte Vite neu.
                    </p>
                </div>
            </div>
        );
    }

    return <div ref={containerRef} className="h-full w-full overflow-hidden rounded-md" />;
}

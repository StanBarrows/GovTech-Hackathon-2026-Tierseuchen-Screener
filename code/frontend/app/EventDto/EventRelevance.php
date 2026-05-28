<?php

namespace App\EventDto;

final class EventRelevance
{
    private const EARTH_KM = 6371.0;

    public static function haversineKm(float $lat1, float $lng1, float $lat2, float $lng2): float
    {
        $toRad = static fn (float $d): float => $d * M_PI / 180.0;

        $dLat = $toRad($lat2 - $lat1);
        $dLng = $toRad($lng2 - $lng1);
        $a = $toRad($lat1);
        $b = $toRad($lat2);

        $h = sin($dLat / 2) ** 2 + cos($a) * cos($b) * sin($dLng / 2) ** 2;

        return 2 * self::EARTH_KM * asin(sqrt($h));
    }

    public static function decay(float $distanceKm, float $radiusKm): float
    {
        if ($radiusKm <= 0) {
            return 0.0;
        }

        return exp(-$distanceKm / $radiusKm);
    }

    public static function relevance(float $weight, float $distanceKm, float $radiusKm): float
    {
        return $weight * self::decay($distanceKm, $radiusKm);
    }
}

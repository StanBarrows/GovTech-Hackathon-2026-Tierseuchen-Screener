<?php

namespace App\Services\Lindas;

class IriHelper
{
    public static function localName(?string $iri): ?string
    {
        if ($iri === null || $iri === '') {
            return null;
        }

        $fragment = parse_url($iri, PHP_URL_FRAGMENT);

        if (is_string($fragment) && $fragment !== '') {
            return $fragment;
        }

        $path = parse_url($iri, PHP_URL_PATH);

        if (! is_string($path) || $path === '') {
            return $iri;
        }

        $segments = explode('/', trim($path, '/'));

        return $segments[array_key_last($segments)] ?: $iri;
    }

    public static function label(?string $label, ?string $iri): ?string
    {
        if ($label !== null && $label !== '') {
            return $label;
        }

        return self::localName($iri);
    }
}

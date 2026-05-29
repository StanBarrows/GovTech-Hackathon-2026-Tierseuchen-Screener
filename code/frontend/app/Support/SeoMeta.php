<?php

namespace App\Support;

use Illuminate\Http\Request;

class SeoMeta
{
    /**
     * @param  array<string, mixed>  $overrides
     * @return array<string, string|null>
     */
    public static function forPage(array $overrides = [], ?Request $request = null): array
    {
        $request ??= request();

        $siteName = (string) config('seo.site_name');
        $separator = (string) config('seo.title_separator');
        $title = isset($overrides['title']) ? (string) $overrides['title'] : null;

        $fullTitle = $title !== null && $title !== ''
            ? $title.$separator.$siteName
            : $siteName;

        $imagePath = (string) ($overrides['image'] ?? config('seo.default_og_image'));
        $canonical = (string) ($overrides['canonical'] ?? $request->url());

        return [
            'title' => $title,
            'fullTitle' => $fullTitle,
            'description' => (string) ($overrides['description'] ?? config('seo.default_description')),
            'image' => self::absoluteUrl($imagePath),
            'canonical' => self::absoluteUrl($canonical),
            'robots' => isset($overrides['robots']) ? (string) $overrides['robots'] : null,
            'type' => (string) ($overrides['type'] ?? 'website'),
            'siteName' => $siteName,
            'locale' => str_replace('_', '-', (string) config('seo.locale')),
            'twitterCard' => (string) config('seo.twitter_card'),
            'themeColor' => (string) config('seo.theme_color'),
        ];
    }

    private static function absoluteUrl(string $pathOrUrl): string
    {
        if (str_starts_with($pathOrUrl, 'http://') || str_starts_with($pathOrUrl, 'https://')) {
            return $pathOrUrl;
        }

        $base = rtrim((string) config('seo.site_url'), '/');
        $path = '/'.ltrim($pathOrUrl, '/');

        return $base.$path;
    }
}

@php
    $seo = $page['props']['seo'] ?? null;

    if (! is_array($seo)) {
        $seo = \App\Support\SeoMeta::forPage();
    }
@endphp

<title>{{ $seo['fullTitle'] }}</title>
<meta name="description" content="{{ $seo['description'] }}">
@if (! empty($seo['robots']))
<meta name="robots" content="{{ $seo['robots'] }}">
@endif
<link rel="canonical" href="{{ $seo['canonical'] }}">
<meta property="og:title" content="{{ $seo['fullTitle'] }}">
<meta property="og:description" content="{{ $seo['description'] }}">
<meta property="og:image" content="{{ $seo['image'] }}">
<meta property="og:url" content="{{ $seo['canonical'] }}">
<meta property="og:type" content="{{ $seo['type'] }}">
<meta property="og:site_name" content="{{ $seo['siteName'] }}">
<meta property="og:locale" content="{{ $seo['locale'] }}">
<meta name="twitter:card" content="{{ $seo['twitterCard'] }}">
<meta name="twitter:title" content="{{ $seo['fullTitle'] }}">
<meta name="twitter:description" content="{{ $seo['description'] }}">
<meta name="twitter:image" content="{{ $seo['image'] }}">
<meta name="theme-color" content="{{ $seo['themeColor'] }}">

<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Third Party Services
    |--------------------------------------------------------------------------
    |
    | This file is for storing the credentials for third party services such
    | as Mailgun, Postmark, AWS and more. This file provides the de facto
    | location for this type of information, allowing packages to have
    | a conventional file to locate the various service credentials.
    |
    */

    'postmark' => [
        'key' => env('POSTMARK_API_KEY'),
    ],

    'resend' => [
        'key' => env('RESEND_API_KEY'),
    ],

    'ses' => [
        'key' => env('AWS_ACCESS_KEY_ID'),
        'secret' => env('AWS_SECRET_ACCESS_KEY'),
        'region' => env('AWS_DEFAULT_REGION', 'us-east-1'),
    ],

    'slack' => [
        'notifications' => [
            'bot_user_oauth_token' => env('SLACK_BOT_USER_OAUTH_TOKEN'),
            'channel' => env('SLACK_BOT_USER_DEFAULT_CHANNEL'),
        ],
    ],

    'lindas' => [
        'sparql_endpoint' => env('LINDAS_SPARQL_ENDPOINT', 'https://int.lindas.admin.ch/query'),
        'graph_uri' => env('LINDAS_GRAPH_URI', 'https://lindas.admin.ch/fsvo/govtech26-tierseuchen-screener'),
        'timeout' => (int) env('LINDAS_SPARQL_TIMEOUT', 30),
        'queries_path' => env('LINDAS_QUERIES_PATH'),
        'cache_ttl' => (int) env('LINDAS_CACHE_TTL', 900),
    ],

];

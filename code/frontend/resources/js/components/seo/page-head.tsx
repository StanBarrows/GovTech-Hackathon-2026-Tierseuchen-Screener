import { Head } from '@inertiajs/react';

import type { SeoMeta } from '@/types/seo';

type Props = {
    seo?: SeoMeta;
};

export function PageHead({ seo }: Props) {
    if (! seo) {
        return null;
    }

    return (
        <Head title={seo.fullTitle}>
            <meta head-key="description" name="description" content={seo.description} />
            {seo.robots ? (
                <meta head-key="robots" name="robots" content={seo.robots} />
            ) : null}
            <link head-key="canonical" rel="canonical" href={seo.canonical} />
            <meta head-key="og:title" property="og:title" content={seo.fullTitle} />
            <meta head-key="og:description" property="og:description" content={seo.description} />
            <meta head-key="og:image" property="og:image" content={seo.image} />
            <meta head-key="og:url" property="og:url" content={seo.canonical} />
            <meta head-key="og:type" property="og:type" content={seo.type} />
            <meta head-key="og:site_name" property="og:site_name" content={seo.siteName} />
            <meta head-key="og:locale" property="og:locale" content={seo.locale} />
            <meta head-key="twitter:card" name="twitter:card" content={seo.twitterCard} />
            <meta head-key="twitter:title" name="twitter:title" content={seo.fullTitle} />
            <meta
                head-key="twitter:description"
                name="twitter:description"
                content={seo.description}
            />
            <meta head-key="twitter:image" name="twitter:image" content={seo.image} />
            <meta head-key="theme-color" name="theme-color" content={seo.themeColor} />
        </Head>
    );
}

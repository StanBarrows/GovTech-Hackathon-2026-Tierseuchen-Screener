export type SeoMeta = {
    title: string | null;
    fullTitle: string;
    description: string;
    image: string;
    canonical: string;
    robots: string | null;
    type: string;
    siteName: string;
    locale: string;
    twitterCard: string;
    themeColor: string;
};

export type SeoDefaults = {
    siteName: string;
    siteUrl: string;
    defaultDescription: string;
    defaultOgImage: string;
};

import { Link, usePage } from '@inertiajs/react';

import {
    NavigationMenu,
    NavigationMenuItem,
    NavigationMenuLink,
    NavigationMenuList,
} from '@/components/ui/navigation-menu';

type Props = {
    title: string;
    subtitle?: string;
};

const nav = [
    { href: '/dashboard/map', label: 'Karte' },
];

export default function LagebildHeader({ title, subtitle }: Props) {
    const { url } = usePage();

    return (
        <header className="flex items-center justify-between gap-6 border-b bg-card px-6 py-3">
            <div className="flex items-baseline gap-3">
                <h1 className="text-lg font-semibold">{title}</h1>
                {subtitle && (
                    <span className="text-xs text-muted-foreground">{subtitle}</span>
                )}
            </div>

            <NavigationMenu>
                <NavigationMenuList>
                    {nav.map((item) => {
                        const active = url === item.href;
                        return (
                            <NavigationMenuItem key={item.href}>
                                <NavigationMenuLink
                                    asChild
                                    active={active}
                                    className="px-3 py-1.5 text-sm"
                                >
                                    <Link href={item.href}>{item.label}</Link>
                                </NavigationMenuLink>
                            </NavigationMenuItem>
                        );
                    })}
                </NavigationMenuList>
            </NavigationMenu>
        </header>
    );
}

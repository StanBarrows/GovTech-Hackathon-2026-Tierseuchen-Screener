import type { PropsWithChildren } from 'react';

import { TooltipProvider } from '@/components/ui/tooltip';

export default function DashboardLayout({ children }: PropsWithChildren) {
    return (
        <TooltipProvider delayDuration={0}>
            <div className="flex min-h-screen flex-col bg-background">{children}</div>
        </TooltipProvider>
    );
}

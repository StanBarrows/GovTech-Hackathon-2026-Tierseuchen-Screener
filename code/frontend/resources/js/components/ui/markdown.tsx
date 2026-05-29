import ReactMarkdown from 'react-markdown';
import type { Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { cn } from '@/lib/utils';

const components: Components = {
    h1: ({ className, ...props }) => (
        <h1
            className={cn('mt-4 text-base font-semibold text-foreground first:mt-0', className)}
            {...props}
        />
    ),
    h2: ({ className, ...props }) => (
        <h2
            className={cn('mt-4 text-sm font-semibold text-foreground first:mt-0', className)}
            {...props}
        />
    ),
    h3: ({ className, ...props }) => (
        <h3
            className={cn('mt-3 text-sm font-medium text-foreground first:mt-0', className)}
            {...props}
        />
    ),
    p: ({ className, ...props }) => (
        <p
            className={cn('text-sm leading-relaxed text-muted-foreground', className)}
            {...props}
        />
    ),
    strong: ({ className, ...props }) => (
        <strong className={cn('font-semibold text-foreground', className)} {...props} />
    ),
    ul: ({ className, ...props }) => (
        <ul
            className={cn('list-disc space-y-1 pl-5 text-sm text-muted-foreground', className)}
            {...props}
        />
    ),
    ol: ({ className, ...props }) => (
        <ol
            className={cn('list-decimal space-y-1 pl-5 text-sm text-muted-foreground', className)}
            {...props}
        />
    ),
    li: ({ className, ...props }) => (
        <li className={cn('text-sm text-muted-foreground', className)} {...props} />
    ),
    a: ({ className, ...props }) => (
        <a
            target="_blank"
            rel="noopener noreferrer"
            className={cn('text-primary underline-offset-4 hover:underline', className)}
            {...props}
        />
    ),
};

type MarkdownProps = {
    children: string;
    className?: string;
};

export function Markdown({ children, className }: MarkdownProps) {
    return (
        <div className={cn('space-y-3', className)}>
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
                {children}
            </ReactMarkdown>
        </div>
    );
}

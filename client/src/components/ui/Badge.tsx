import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        default: "bg-[var(--color-surface-2)] text-[var(--color-ink-soft)]",
        primary: "bg-[var(--color-primary-soft)] text-[var(--color-primary)]",
        citation: "bg-[var(--color-citation-soft)] text-[var(--color-citation)] font-mono-tag",
        success: "bg-green-100 text-green-700 dark:bg-green-950 dark:text-green-400",
        warning: "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-400",
        danger: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400",
        outline: "border border-[var(--color-border)] text-[var(--color-ink-soft)]",
      },
    },
    defaultVariants: { variant: "default" },
  }
);

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

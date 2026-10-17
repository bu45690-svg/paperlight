import * as TabsPrimitive from "@radix-ui/react-tabs";
import { cn } from "@/lib/utils";

export const Tabs = TabsPrimitive.Root;

export function TabsList({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.List>) {
  return (
    <TabsPrimitive.List
      className={cn(
        "inline-flex h-11 items-center gap-1 rounded-lg bg-[var(--color-surface-2)] p-1",
        className
      )}
      {...props}
    />
  );
}

export function TabsTrigger({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.Trigger>) {
  return (
    <TabsPrimitive.Trigger
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-3 h-9 text-sm font-medium text-[var(--color-ink-soft)] transition-colors data-[state=active]:bg-[var(--color-surface)] data-[state=active]:text-[var(--color-ink)] data-[state=active]:shadow-sm",
        className
      )}
      {...props}
    />
  );
}

export function TabsContent({ className, ...props }: React.ComponentProps<typeof TabsPrimitive.Content>) {
  return (
    <TabsPrimitive.Content
      className={cn("mt-4 focus-visible:outline-none animate-fade-in-up", className)}
      {...props}
    />
  );
}

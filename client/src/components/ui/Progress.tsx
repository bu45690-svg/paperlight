import * as ProgressPrimitive from "@radix-ui/react-progress";
import { cn } from "@/lib/utils";

export function Progress({ value, className }: { value: number; className?: string }) {
  return (
    <ProgressPrimitive.Root
      className={cn("relative h-2 w-full overflow-hidden rounded-full bg-[var(--color-surface-2)]", className)}
      value={value}
    >
      <ProgressPrimitive.Indicator
        className="h-full bg-[var(--color-primary)] transition-transform duration-300 ease-out"
        style={{ transform: `translateX(-${100 - value}%)` }}
      />
    </ProgressPrimitive.Root>
  );
}

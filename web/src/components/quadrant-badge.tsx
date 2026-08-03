import { Quadrant } from "@/lib/api-client";
import { cn } from "@/lib/utils";

const QUADRANT_STYLES: Record<Quadrant, string> = {
  [Quadrant.Q1]: "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300",
  [Quadrant.Q2]: "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300",
  [Quadrant.Q3]: "bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-300",
  [Quadrant.Q4]: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300",
};

export function QuadrantBadge({ quadrant }: { quadrant: Quadrant }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        QUADRANT_STYLES[quadrant],
      )}
    >
      {quadrant}
    </span>
  );
}

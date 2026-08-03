"use client";

import { Star } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { QuadrantBadge } from "@/components/quadrant-badge";
import { TaskStatus, type TaskRead } from "@/lib/api-client";
import { cn } from "@/lib/utils";

export function TaskCard({
  task,
  onToggleComplete,
  onToggleBigRock,
  dragHandleProps,
  className,
}: {
  task: TaskRead;
  onToggleComplete: (task: TaskRead) => void;
  onToggleBigRock?: (task: TaskRead) => void;
  dragHandleProps?: Record<string, unknown>;
  className?: string;
}) {
  const done = task.status === TaskStatus.DONE;

  return (
    <div
      className={cn(
        "flex items-start gap-2 rounded-md border bg-card p-2 text-sm shadow-sm",
        className,
      )}
      {...dragHandleProps}
    >
      <Checkbox
        checked={done}
        onCheckedChange={() => onToggleComplete(task)}
        className="mt-0.5"
      />
      <div className="min-w-0 flex-1">
        <p className={cn("truncate", done && "text-muted-foreground line-through")}>
          {task.title}
        </p>
        <div className="mt-1">
          <QuadrantBadge quadrant={task.quadrant} />
        </div>
      </div>
      {onToggleBigRock && (
        <button
          type="button"
          aria-label={task.is_big_rock ? "Unpin big rock" : "Pin as big rock"}
          onClick={() => onToggleBigRock(task)}
          className="shrink-0"
        >
          <Star
            className={cn(
              "size-4",
              task.is_big_rock ? "fill-amber-400 text-amber-500" : "text-muted-foreground",
            )}
          />
        </button>
      )}
    </div>
  );
}

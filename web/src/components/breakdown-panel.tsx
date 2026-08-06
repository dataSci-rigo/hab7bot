"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { QuadrantBadge } from "@/components/quadrant-badge";
import { useAcceptBreakdown, useBreakdownProject } from "@/lib/hooks";
import type { BreakdownProposal, BreakdownTask } from "@/lib/api-client";
import { ApiError } from "@/lib/api-client";

function taskKey(milestoneIdx: number, taskIdx: number) {
  return `${milestoneIdx}:${taskIdx}`;
}

export function BreakdownPanel({ projectId }: { projectId: string }) {
  const breakdown = useBreakdownProject();
  const acceptBreakdown = useAcceptBreakdown();
  const [proposal, setProposal] = useState<BreakdownProposal | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  async function handleGenerate() {
    try {
      const result = await breakdown.mutateAsync(projectId);
      setProposal(result);
      const all = new Set<string>();
      result.milestones.forEach((m, mi) => m.tasks.forEach((_t, ti) => all.add(taskKey(mi, ti))));
      setSelected(all);
    } catch {
      toast.error("AI is currently unavailable. Try again.");
    }
  }

  function toggle(key: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  async function handleAccept() {
    if (!proposal) return;
    const chosen: BreakdownTask[] = [];
    proposal.milestones.forEach((m, mi) =>
      m.tasks.forEach((t, ti) => {
        if (selected.has(taskKey(mi, ti))) chosen.push(t);
      }),
    );
    if (chosen.length === 0) return;
    try {
      await acceptBreakdown.mutateAsync({ projectId, selected: chosen });
      toast.success(`Added ${chosen.length} task(s)`);
      setProposal(null);
    } catch {
      toast.error("Couldn't create tasks");
    }
  }

  if (!proposal) {
    return (
      <div className="space-y-2">
        <Button variant="outline" size="sm" onClick={handleGenerate} disabled={breakdown.isPending}>
          {breakdown.isPending ? "Breaking down…" : "Break down with AI"}
        </Button>
        {breakdown.isError && (
          <p className="text-sm text-destructive">
            {breakdown.error instanceof ApiError && breakdown.error.status === 503
              ? "AI is currently unavailable."
              : "Something went wrong."}{" "}
            <button className="underline" onClick={handleGenerate}>
              Retry
            </button>
          </p>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4 rounded-md border p-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold">AI breakdown proposal</p>
        <Button variant="ghost" size="sm" onClick={() => setProposal(null)}>
          Discard
        </Button>
      </div>

      {proposal.milestones.map((milestone, mi) => (
        <div key={mi} className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground">{milestone.title}</p>
          {milestone.tasks.map((task, ti) => {
            const key = taskKey(mi, ti);
            return (
              <label key={key} className="flex items-center gap-2 rounded-md border p-2 text-sm">
                <Checkbox checked={selected.has(key)} onCheckedChange={() => toggle(key)} />
                <span className="flex-1">{task.title}</span>
                {task.estimate_minutes != null && (
                  <span className="text-xs text-muted-foreground">{task.estimate_minutes}m</span>
                )}
                {task.quadrant && <QuadrantBadge quadrant={task.quadrant} />}
                {!!task.suggested_week_offset && task.suggested_week_offset > 0 && (
                  <span className="text-xs text-muted-foreground">
                    +{task.suggested_week_offset}w
                  </span>
                )}
              </label>
            );
          })}
        </div>
      ))}

      {(proposal.questions?.length ?? 0) > 0 && (
        <div className="rounded-md bg-accent/50 p-2 text-xs">
          <p className="font-medium">Questions from the AI:</p>
          <ul className="list-inside list-disc">
            {proposal.questions?.map((q, i) => (
              <li key={i}>{q}</li>
            ))}
          </ul>
        </div>
      )}
      {(proposal.assumptions?.length ?? 0) > 0 && (
        <div className="text-xs text-muted-foreground">
          <p className="font-medium">Assumptions:</p>
          <ul className="list-inside list-disc">
            {proposal.assumptions?.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>
      )}

      <Button size="sm" onClick={handleAccept} disabled={selected.size === 0 || acceptBreakdown.isPending}>
        Add {selected.size} task{selected.size === 1 ? "" : "s"}
      </Button>
    </div>
  );
}

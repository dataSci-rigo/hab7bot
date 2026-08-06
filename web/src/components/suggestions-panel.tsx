"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useAcceptSuggestion, useSuggestProjects } from "@/lib/hooks";
import { ApiError, type ProjectSuggestion } from "@/lib/api-client";

export function SuggestionsPanel() {
  const suggestMutation = useSuggestProjects();
  const acceptMutation = useAcceptSuggestion();
  const [suggestions, setSuggestions] = useState<ProjectSuggestion[] | null>(null);

  async function handleSuggest() {
    try {
      const result = await suggestMutation.mutateAsync();
      setSuggestions(result);
    } catch {
      toast.error("AI is currently unavailable. Try again.");
    }
  }

  async function handleAccept(suggestion: ProjectSuggestion) {
    try {
      await acceptMutation.mutateAsync(suggestion);
      setSuggestions((prev) => prev?.filter((s) => s !== suggestion) ?? null);
      toast.success(`Created project "${suggestion.title}"`);
    } catch {
      toast.error("Couldn't create project");
    }
  }

  return (
    <div className="space-y-3">
      <Button variant="outline" size="sm" onClick={handleSuggest} disabled={suggestMutation.isPending}>
        {suggestMutation.isPending ? "Thinking…" : "Suggest projects"}
      </Button>
      {suggestMutation.isError && (
        <p className="text-sm text-destructive">
          {suggestMutation.error instanceof ApiError && suggestMutation.error.status === 503
            ? "AI is currently unavailable."
            : "Something went wrong."}{" "}
          <button className="underline" onClick={handleSuggest}>
            Retry
          </button>
        </p>
      )}

      {suggestions && suggestions.length === 0 && (
        <p className="text-sm text-muted-foreground">No suggestions right now.</p>
      )}

      {suggestions?.map((s, i) => (
        <div key={i} className="space-y-2 rounded-md border p-3 text-sm">
          <div className="flex items-center justify-between">
            <p className="font-medium">{s.title}</p>
            <Button size="sm" onClick={() => handleAccept(s)} disabled={acceptMutation.isPending}>
              Accept
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            {s.role_name}
            {s.goal_title ? ` · ${s.goal_title}` : ""} · {s.quadrant_profile}
          </p>
          <p>{s.rationale}</p>
          <ul className="list-inside list-disc text-xs text-muted-foreground">
            {s.first_three_tasks.map((t, ti) => (
              <li key={ti}>{t}</li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

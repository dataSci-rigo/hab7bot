"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  useGenerateWeeklyReview,
  useSaveReflection,
  useWeeklyReview,
} from "@/lib/hooks";
import type { WeeklyReviewRead } from "@/lib/api-client";
import { currentIsoWeek, shiftIsoWeek } from "@/lib/iso-week";

const QUADRANT_LABELS: Record<string, string> = {
  Q1: "Q1 — Urgent & Important",
  Q2: "Q2 — Not Urgent & Important",
  Q3: "Q3 — Urgent & Not Important",
  Q4: "Q4 — Not Urgent & Not Important",
};

interface WeekStats {
  big_rock_total: number;
  big_rock_completed: number;
  big_rock_completion_rate: number | null;
  quadrant_effort_minutes: Record<string, number>;
  role_effort_minutes: Record<string, number>;
  carry_over_count: number;
  avg_capture_to_completion_hours: number | null;
}

interface WeekAnalysisSuggestion {
  change: string;
  why: string;
  how: string;
}

interface WeekAnalysisView {
  summary: string;
  wins: string[];
  concerns: string[];
  patterns: string[];
  suggestions: WeekAnalysisSuggestion[];
  suggested_big_rock_candidates_next_week: string[];
  q2_percent_trend: string;
}

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  );
}

function StatsSection({ stats }: { stats: WeekStats }) {
  const bigRockRate = stats.big_rock_completion_rate;
  const quadrantEffort = (stats.quadrant_effort_minutes ?? {}) as Record<string, number>;
  const roleEffort = (stats.role_effort_minutes ?? {}) as Record<string, number>;

  return (
    <section className="space-y-3">
      <h2 className="text-sm font-semibold text-muted-foreground">Stats</h2>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <StatTile
          label="Big rocks completed"
          value={
            bigRockRate === null
              ? "no big rocks pinned"
              : `${stats.big_rock_completed}/${stats.big_rock_total} (${Math.round(bigRockRate * 100)}%)`
          }
        />
        <StatTile label="Carried over" value={String(stats.carry_over_count)} />
        <StatTile
          label="Capture → completion"
          value={
            stats.avg_capture_to_completion_hours === null
              ? "—"
              : `${Math.round(stats.avg_capture_to_completion_hours)}h avg`
          }
        />
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {Object.entries(quadrantEffort).map(([q, minutes]) => (
          <StatTile key={q} label={QUADRANT_LABELS[q] ?? q} value={`${minutes} min`} />
        ))}
      </div>

      {Object.keys(roleEffort).length > 0 && (
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Effort by role</p>
          <div className="flex flex-wrap gap-2">
            {Object.entries(roleEffort).map(([role, minutes]) => (
              <span key={role} className="rounded-full border px-3 py-1 text-xs">
                {role}: {minutes} min
              </span>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

function AnalysisSection({ analysis }: { analysis: WeekAnalysisView }) {
  const suggestions = analysis.suggestions ?? [];

  return (
    <section className="space-y-3">
      <h2 className="text-sm font-semibold text-muted-foreground">AI analysis</h2>
      <p className="text-sm">{analysis.summary}</p>

      {analysis.wins?.length > 0 && (
        <div>
          <p className="text-xs font-medium text-muted-foreground">Wins</p>
          <ul className="list-disc space-y-1 pl-5 text-sm">
            {analysis.wins.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {analysis.concerns?.length > 0 && (
        <div>
          <p className="text-xs font-medium text-muted-foreground">Concerns</p>
          <ul className="list-disc space-y-1 pl-5 text-sm">
            {analysis.concerns.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      )}

      {analysis.patterns?.length > 0 && (
        <div>
          <p className="text-xs font-medium text-muted-foreground">Patterns</p>
          <ul className="list-disc space-y-1 pl-5 text-sm">
            {analysis.patterns.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </div>
      )}

      {suggestions.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground">Suggestions</p>
          {suggestions.map((s, i) => (
            <div key={i} className="rounded-md border p-2 text-sm">
              <p className="font-medium">{s.change}</p>
              <p className="text-xs text-muted-foreground">{s.why}</p>
              <p className="text-xs">{s.how}</p>
            </div>
          ))}
        </div>
      )}

      {analysis.suggested_big_rock_candidates_next_week?.length > 0 && (
        <div>
          <p className="text-xs font-medium text-muted-foreground">
            Big rock candidates for next week
          </p>
          <div className="flex flex-wrap gap-2">
            {analysis.suggested_big_rock_candidates_next_week.map((c, i) => (
              <span key={i} className="rounded-full border px-3 py-1 text-xs">
                {c}
              </span>
            ))}
          </div>
        </div>
      )}

      <p className="text-xs text-muted-foreground">Q2 trend: {analysis.q2_percent_trend}</p>
    </section>
  );
}

function ReviewBody({
  isoWeek,
  review,
}: {
  isoWeek: string;
  review: WeeklyReviewRead | undefined;
}) {
  const generateReview = useGenerateWeeklyReview();
  const saveReflection = useSaveReflection();
  const [reflection, setReflection] = useState(review?.reflection ?? "");

  async function handleGenerate(force: boolean) {
    await generateReview.mutateAsync({ isoWeek, force });
    toast.success(force ? "Analysis regenerated" : "Analysis generated");
  }

  async function handleSaveReflection() {
    await saveReflection.mutateAsync({ isoWeek, reflection });
    toast.success("Reflection saved");
  }

  return (
    <>
      {review ? (
        <>
          {review.stats && <StatsSection stats={review.stats as unknown as WeekStats} />}
          {review.ai_analysis ? (
            <AnalysisSection analysis={review.ai_analysis as unknown as WeekAnalysisView} />
          ) : (
            <p className="text-sm text-muted-foreground">No AI analysis on this review yet.</p>
          )}
          <Button
            size="sm"
            variant="outline"
            disabled={generateReview.isPending}
            onClick={() => handleGenerate(true)}
          >
            {generateReview.isPending ? "Regenerating…" : "Regenerate analysis"}
          </Button>
        </>
      ) : (
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">No review generated for this week yet.</p>
          <Button
            size="sm"
            disabled={generateReview.isPending}
            onClick={() => handleGenerate(false)}
          >
            {generateReview.isPending ? "Generating…" : "Generate review"}
          </Button>
        </div>
      )}

      <section className="space-y-2">
        <h2 className="text-sm font-semibold text-muted-foreground">Your reflection</h2>
        <Textarea
          value={reflection}
          onChange={(e) => setReflection(e.target.value)}
          rows={4}
          placeholder="How did this week actually go?"
        />
        <Button size="sm" disabled={saveReflection.isPending} onClick={handleSaveReflection}>
          {saveReflection.isPending ? "Saving…" : "Save reflection"}
        </Button>
      </section>
    </>
  );
}

export default function WeeklyReviewPage() {
  const [isoWeek, setIsoWeek] = useState(currentIsoWeek());
  const { data: review, isLoading } = useWeeklyReview(isoWeek);

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" onClick={() => setIsoWeek((w) => shiftIsoWeek(w, -1))}>
          ← Prev
        </Button>
        <h1 className="text-lg font-semibold">Weekly Review — {isoWeek}</h1>
        <Button variant="outline" size="sm" onClick={() => setIsoWeek((w) => shiftIsoWeek(w, 1))}>
          Next →
        </Button>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <ReviewBody key={review?.id ?? isoWeek} isoWeek={isoWeek} review={review} />
      )}
    </div>
  );
}

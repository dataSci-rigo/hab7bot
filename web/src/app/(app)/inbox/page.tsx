"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { QuickAddBox } from "@/components/quick-add-box";
import {
  useDeleteTask,
  useInboxAiTriage,
  useProjects,
  useRoles,
  useTasks,
  useUpdateTask,
} from "@/lib/hooks";
import {
  ApiError,
  Quadrant,
  TaskStatus,
  type InboxTriageSuggestion,
  type TaskRead,
  type TaskUpdate,
} from "@/lib/api-client";

const QUADRANTS = [Quadrant.Q1, Quadrant.Q2, Quadrant.Q3, Quadrant.Q4];

type BulkField = "role_id" | "project_id" | "quadrant" | "scheduled_week";

function InboxRow({
  task,
  suggestion,
  onDismissSuggestion,
}: {
  task: TaskRead;
  suggestion?: InboxTriageSuggestion;
  onDismissSuggestion: (taskId: string) => void;
}) {
  const { data: roles } = useRoles();
  const { data: projects } = useProjects();
  const updateTask = useUpdateTask();
  const deleteTask = useDeleteTask();
  const [week, setWeek] = useState(task.scheduled_week ?? "");

  function patch(data: TaskUpdate) {
    updateTask.mutate({ id: task.id, data });
  }

  // Assigning a week or project is what "triaging out of the inbox" means
  // per SPEC's Inbox model — advance status so the task leaves this list.
  function patchAndTriage(data: TaskUpdate) {
    const leavesInbox = data.scheduled_week || data.project_id;
    const shouldAdvance = task.status === TaskStatus.INBOX && leavesInbox;
    patch(shouldAdvance ? { ...data, status: TaskStatus.PLANNED } : data);
  }

  function applySuggestion() {
    if (!suggestion) return;
    patchAndTriage({
      role_id: suggestion.role_id ?? undefined,
      quadrant: suggestion.quadrant,
      project_id: suggestion.project_id,
    });
    onDismissSuggestion(task.id);
  }

  return (
    <div className="space-y-1">
      <div className="flex flex-wrap items-center gap-2 rounded-md border p-2 text-sm">
        <span className="min-w-40 flex-1 truncate">{task.title}</span>

        <Select value={task.role_id} onValueChange={(v) => patch({ role_id: v })}>
          <SelectTrigger className="w-36">
            <SelectValue placeholder="Role" />
          </SelectTrigger>
          <SelectContent>
            {roles?.map((r) => (
              <SelectItem key={r.id} value={r.id}>
                {r.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={task.project_id ?? "none"}
          onValueChange={(v) => patchAndTriage({ project_id: v === "none" ? null : v })}
        >
          <SelectTrigger className="w-36">
            <SelectValue placeholder="Project" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">No project</SelectItem>
            {projects?.map((p) => (
              <SelectItem key={p.id} value={p.id}>
                {p.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={task.quadrant} onValueChange={(v) => patch({ quadrant: v as Quadrant })}>
          <SelectTrigger className="w-20">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {QUADRANTS.map((q) => (
              <SelectItem key={q} value={q}>
                {q}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Input
          value={week}
          onChange={(e) => setWeek(e.target.value)}
          onBlur={() => patchAndTriage({ scheduled_week: week || null })}
          placeholder="YYYY-Www"
          className="w-28"
        />

        <Button
          variant="ghost"
          size="sm"
          onClick={async () => {
            try {
              await deleteTask.mutateAsync(task.id);
            } catch {
              toast.error("Couldn't delete task");
            }
          }}
        >
          Delete
        </Button>
      </div>
      {suggestion && (
        <div className="flex flex-wrap items-center gap-2 rounded-md border border-dashed bg-accent/40 p-2 text-xs">
          <span className="font-medium">AI suggests:</span>
          <span>
            {suggestion.role_name ?? "—"} · {suggestion.quadrant}
            {suggestion.is_big_rock_candidate ? " · big rock" : ""}
            {suggestion.project_title ? ` · ${suggestion.project_title}` : ""}
          </span>
          <Button size="sm" variant="outline" onClick={applySuggestion}>
            Apply
          </Button>
          <Button size="sm" variant="ghost" onClick={() => onDismissSuggestion(task.id)}>
            Dismiss
          </Button>
        </div>
      )}
    </div>
  );
}

export default function InboxPage() {
  const { data: tasks, isLoading } = useTasks({ status: TaskStatus.INBOX });
  const { data: roles } = useRoles();
  const { data: projects } = useProjects();
  const updateTask = useUpdateTask();
  const deleteTask = useDeleteTask();
  const aiTriage = useInboxAiTriage();

  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [bulkField, setBulkField] = useState<BulkField>("role_id");
  const [bulkValue, setBulkValue] = useState("");
  const [suggestions, setSuggestions] = useState<Map<string, InboxTriageSuggestion>>(new Map());

  function dismissSuggestion(taskId: string) {
    setSuggestions((prev) => {
      const next = new Map(prev);
      next.delete(taskId);
      return next;
    });
  }

  async function handleAiTriage() {
    try {
      const result = await aiTriage.mutateAsync();
      setSuggestions(new Map(result.map((s) => [s.task_id, s])));
      if (result.length === 0) toast.info("Nothing to triage.");
    } catch (err) {
      toast.error(
        err instanceof ApiError && err.status === 503
          ? "AI is currently unavailable. Try again."
          : "AI triage failed.",
      );
    }
  }

  function toggleSelected(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function applyBulkUpdate() {
    if (selected.size === 0 || !bulkValue) return;
    const data: TaskUpdate =
      bulkField === "project_id"
        ? { project_id: bulkValue === "none" ? null : bulkValue }
        : { [bulkField]: bulkValue };
    // Every row on this page is status=inbox; assigning a project or week is
    // what triaging out of the inbox means, so advance status along with it.
    if (bulkField === "project_id" || bulkField === "scheduled_week") {
      data.status = TaskStatus.PLANNED;
    }
    try {
      await Promise.all([...selected].map((id) => updateTask.mutateAsync({ id, data })));
      toast.success(`Updated ${selected.size} task(s)`);
      setSelected(new Set());
    } catch {
      toast.error("Bulk update failed");
    }
  }

  async function applyBulkDelete() {
    if (selected.size === 0) return;
    try {
      await Promise.all([...selected].map((id) => deleteTask.mutateAsync(id)));
      toast.success(`Deleted ${selected.size} task(s)`);
      setSelected(new Set());
    } catch {
      toast.error("Bulk delete failed");
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-semibold">Inbox</h1>

      <div className="flex items-center gap-2">
        <QuickAddBox placeholder="Capture something…" allowAiCapture />
        <Button variant="outline" size="sm" onClick={handleAiTriage} disabled={aiTriage.isPending}>
          {aiTriage.isPending ? "Triaging…" : "AI triage"}
        </Button>
      </div>

      {selected.size > 0 && (
        <div className="flex flex-wrap items-center gap-2 rounded-md border bg-accent/50 p-2 text-sm">
          <span>{selected.size} selected</span>
          <Select value={bulkField} onValueChange={(v) => setBulkField(v as BulkField)}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="role_id">Role</SelectItem>
              <SelectItem value="project_id">Project</SelectItem>
              <SelectItem value="quadrant">Quadrant</SelectItem>
              <SelectItem value="scheduled_week">Week</SelectItem>
            </SelectContent>
          </Select>

          {bulkField === "role_id" && (
            <Select value={bulkValue} onValueChange={setBulkValue}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Value" />
              </SelectTrigger>
              <SelectContent>
                {roles?.map((r) => (
                  <SelectItem key={r.id} value={r.id}>
                    {r.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          {bulkField === "project_id" && (
            <Select value={bulkValue} onValueChange={setBulkValue}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Value" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No project</SelectItem>
                {projects?.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          {bulkField === "quadrant" && (
            <Select value={bulkValue} onValueChange={setBulkValue}>
              <SelectTrigger className="w-20">
                <SelectValue placeholder="Value" />
              </SelectTrigger>
              <SelectContent>
                {QUADRANTS.map((q) => (
                  <SelectItem key={q} value={q}>
                    {q}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          {bulkField === "scheduled_week" && (
            <Input
              value={bulkValue}
              onChange={(e) => setBulkValue(e.target.value)}
              placeholder="YYYY-Www"
              className="w-28"
            />
          )}

          <Button size="sm" onClick={applyBulkUpdate} disabled={!bulkValue}>
            Apply
          </Button>
          <Button size="sm" variant="destructive" onClick={applyBulkDelete}>
            Delete selected
          </Button>
        </div>
      )}

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : tasks && tasks.length > 0 ? (
        <div className="space-y-2">
          {tasks.map((task) => (
            <div key={task.id} className="flex items-start gap-2">
              <Checkbox
                checked={selected.has(task.id)}
                onCheckedChange={() => toggleSelected(task.id)}
                className="mt-3"
              />
              <div className="flex-1">
                <InboxRow
                  task={task}
                  suggestion={suggestions.get(task.id)}
                  onDismissSuggestion={dismissSuggestion}
                />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">Inbox is empty.</p>
      )}
    </div>
  );
}

"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCaptureTask, useCreateTask, useRoles } from "@/lib/hooks";
import type { TaskCreate } from "@/lib/api-client";

const AUTO = "auto";

export function QuickAddBox({
  defaultFields,
  defaultRoleId,
  allowAiCapture = false,
  placeholder = "Add a task…",
}: {
  defaultFields?: Partial<TaskCreate>;
  defaultRoleId?: string;
  /** When true, leaving the role on "Auto" routes through §3.4 AI inference
   * (POST /capture) instead of a plain create. Only meaningful when no
   * defaultFields are set — /capture always lands a plain inbox task. */
  allowAiCapture?: boolean;
  placeholder?: string;
}) {
  const { data: roles } = useRoles(true);
  const createTask = useCreateTask();
  const captureTask = useCaptureTask();
  const [title, setTitle] = useState("");
  const [roleId, setRoleId] = useState<string>(defaultRoleId ?? (allowAiCapture ? AUTO : ""));

  const useAi = allowAiCapture && roleId === AUTO;
  const canSubmit = title.trim() && (useAi || roleId);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    try {
      if (useAi) {
        await captureTask.mutateAsync(title.trim());
      } else {
        await createTask.mutateAsync({ title: title.trim(), role_id: roleId, ...defaultFields });
      }
      setTitle("");
      toast.success("Task added");
    } catch {
      toast.error("Couldn't add task");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap gap-2">
      <Input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder={placeholder}
        className="w-full flex-1 basis-full sm:basis-auto"
      />
      <Select value={roleId} onValueChange={setRoleId}>
        <SelectTrigger className="w-40">
          <SelectValue placeholder="Role" />
        </SelectTrigger>
        <SelectContent>
          {allowAiCapture && <SelectItem value={AUTO}>Auto (AI)</SelectItem>}
          {roles?.map((role) => (
            <SelectItem key={role.id} value={role.id}>
              {role.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Button type="submit" disabled={!canSubmit || createTask.isPending || captureTask.isPending}>
        Add
      </Button>
    </form>
  );
}

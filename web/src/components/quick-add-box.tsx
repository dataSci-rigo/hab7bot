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
import { useCreateTask, useRoles } from "@/lib/hooks";
import type { TaskCreate } from "@/lib/api-client";

export function QuickAddBox({
  defaultFields,
  defaultRoleId,
  placeholder = "Add a task…",
}: {
  defaultFields?: Partial<TaskCreate>;
  defaultRoleId?: string;
  placeholder?: string;
}) {
  const { data: roles } = useRoles(true);
  const createTask = useCreateTask();
  const [title, setTitle] = useState("");
  const [roleId, setRoleId] = useState<string>(defaultRoleId ?? "");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !roleId) return;
    try {
      await createTask.mutateAsync({ title: title.trim(), role_id: roleId, ...defaultFields });
      setTitle("");
      toast.success("Task added");
    } catch {
      toast.error("Couldn't add task");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <Input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder={placeholder}
        className="flex-1"
      />
      <Select value={roleId} onValueChange={setRoleId}>
        <SelectTrigger className="w-40">
          <SelectValue placeholder="Role" />
        </SelectTrigger>
        <SelectContent>
          {roles?.map((role) => (
            <SelectItem key={role.id} value={role.id}>
              {role.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Button type="submit" disabled={!title.trim() || !roleId || createTask.isPending}>
        Add
      </Button>
    </form>
  );
}

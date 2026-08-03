"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useCreateProject, useGoals, useProjects, useRoles } from "@/lib/hooks";

export default function ProjectsPage() {
  const { data: projects, isLoading } = useProjects();
  const { data: roles } = useRoles();
  const createProject = useCreateProject();

  const [title, setTitle] = useState("");
  const [roleId, setRoleId] = useState("");
  const [goalId, setGoalId] = useState<string>("none");
  const { data: goals } = useGoals(roleId || undefined);

  const roleName = (id: string) => roles?.find((r) => r.id === id)?.name ?? "—";

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !roleId) return;
    await createProject.mutateAsync({
      title: title.trim(),
      role_id: roleId,
      goal_id: goalId === "none" ? null : goalId,
    });
    setTitle("");
  }

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-lg font-semibold">Projects</h1>

      <form onSubmit={handleCreate} className="flex flex-wrap gap-2">
        <Input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="New project title…"
          className="flex-1"
        />
        <Select value={roleId} onValueChange={setRoleId}>
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
        <Select value={goalId} onValueChange={setGoalId}>
          <SelectTrigger className="w-36">
            <SelectValue placeholder="Goal" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">No goal</SelectItem>
            {goals?.map((g) => (
              <SelectItem key={g.id} value={g.id}>
                {g.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button type="submit" disabled={!title.trim() || !roleId}>
          Add project
        </Button>
      </form>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <div className="space-y-2">
          {projects?.map((project) => (
            <Link
              key={project.id}
              href={`/projects/${project.id}`}
              className="flex items-center justify-between rounded-md border p-3 text-sm hover:bg-accent"
            >
              <div>
                <p className="font-medium">{project.title}</p>
                <p className="text-xs text-muted-foreground">{roleName(project.role_id)}</p>
              </div>
              <Badge variant="secondary">{project.status}</Badge>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

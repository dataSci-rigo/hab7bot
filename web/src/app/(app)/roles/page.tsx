"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import {
  useCreateGoal,
  useCreateRole,
  useDeleteGoal,
  useDeleteRole,
  useGoals,
  useMission,
  useRoles,
  useUpdateMission,
} from "@/lib/hooks";
import type { RoleRead } from "@/lib/api-client";

function MissionEditor() {
  const { data: mission } = useMission();
  if (!mission) return <p className="text-sm text-muted-foreground">Loading…</p>;
  return <MissionForm key={mission.updated_at} initialContent={mission.content} />;
}

function MissionForm({ initialContent }: { initialContent: string }) {
  const updateMission = useUpdateMission();
  const [content, setContent] = useState(initialContent);
  const [dirty, setDirty] = useState(false);

  return (
    <section className="space-y-2">
      <h2 className="text-sm font-semibold text-muted-foreground">Mission Statement</h2>
      <Textarea
        value={content}
        onChange={(e) => {
          setContent(e.target.value);
          setDirty(true);
        }}
        rows={4}
        placeholder="What do you want your life to be about?"
      />
      <Button
        size="sm"
        disabled={!dirty}
        onClick={async () => {
          await updateMission.mutateAsync(content);
          setDirty(false);
          toast.success("Mission statement saved");
        }}
      >
        Save
      </Button>
    </section>
  );
}

function GoalsForRole({ role }: { role: RoleRead }) {
  const { data: goals } = useGoals(role.id);
  const createGoal = useCreateGoal();
  const deleteGoal = useDeleteGoal();
  const [title, setTitle] = useState("");

  return (
    <div className="ml-4 space-y-2">
      {goals?.map((goal) => (
        <div key={goal.id} className="flex items-center gap-2 text-sm">
          <span className="flex-1">{goal.title}</span>
          {goal.target_date && (
            <span className="text-xs text-muted-foreground">{goal.target_date}</span>
          )}
          <Button variant="ghost" size="sm" onClick={() => deleteGoal.mutate(goal.id)}>
            Delete
          </Button>
        </div>
      ))}
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          if (!title.trim()) return;
          await createGoal.mutateAsync({ role_id: role.id, title: title.trim() });
          setTitle("");
        }}
        className="flex gap-2"
      >
        <Input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="New goal…"
          className="h-8 flex-1"
        />
        <Button type="submit" size="sm" variant="outline">
          Add goal
        </Button>
      </form>
    </div>
  );
}

function RoleCard({ role }: { role: RoleRead }) {
  const deleteRole = useDeleteRole();
  return (
    <div className="space-y-2 rounded-md border p-3">
      <div className="flex items-center justify-between">
        <div>
          <p className="font-medium">{role.name}</p>
          {role.description && (
            <p className="text-xs text-muted-foreground">{role.description}</p>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={async () => {
            try {
              await deleteRole.mutateAsync(role.id);
            } catch {
              toast.error("Couldn't delete role");
            }
          }}
        >
          Delete
        </Button>
      </div>
      <GoalsForRole role={role} />
    </div>
  );
}

export default function RolesPage() {
  const { data: roles, isLoading } = useRoles();
  const createRole = useCreateRole();
  const [name, setName] = useState("");

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-lg font-semibold">Roles & Goals</h1>

      <MissionEditor />
      <Separator />

      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-muted-foreground">Roles</h2>
        <form
          onSubmit={async (e) => {
            e.preventDefault();
            if (!name.trim()) return;
            await createRole.mutateAsync({ name: name.trim() });
            setName("");
          }}
          className="flex gap-2"
        >
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="New role name…"
            className="flex-1"
          />
          <Button type="submit">Add role</Button>
        </form>

        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : (
          <div className="space-y-3">
            {roles?.map((role) => (
              <RoleCard key={role.id} role={role} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

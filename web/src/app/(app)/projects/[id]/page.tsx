"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TaskCard } from "@/components/task-card";
import {
  useCompleteTask,
  useDeleteProject,
  useProject,
  useTasks,
  useUncompleteTask,
  useUpdateProject,
} from "@/lib/hooks";
import { ProjectStatus, TaskStatus, type ProjectRead, type TaskRead } from "@/lib/api-client";
import { QuickAddBox } from "@/components/quick-add-box";

const STATUSES = [
  ProjectStatus.IDEA,
  ProjectStatus.ACTIVE,
  ProjectStatus.PAUSED,
  ProjectStatus.DONE,
  ProjectStatus.ABANDONED,
];

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const { data: project } = useProject(params.id);

  if (!project) return <p className="text-sm text-muted-foreground">Loading…</p>;

  return <ProjectDetailForm key={project.id} project={project} />;
}

function ProjectDetailForm({ project }: { project: ProjectRead }) {
  const router = useRouter();
  const { data: tasks } = useTasks({ projectId: project.id });
  const updateProject = useUpdateProject();
  const deleteProject = useDeleteProject();
  const completeTask = useCompleteTask();
  const uncompleteTask = useUncompleteTask();

  const [title, setTitle] = useState(project.title);
  const [notes, setNotes] = useState(project.notes ?? "");
  const [dirty, setDirty] = useState(false);

  function handleToggleComplete(task: TaskRead) {
    if (task.status === TaskStatus.DONE) uncompleteTask.mutate(task.id);
    else completeTask.mutate(task.id);
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <Input
          value={title}
          onChange={(e) => {
            setTitle(e.target.value);
            setDirty(true);
          }}
          className="text-lg font-semibold"
        />
        <Select
          value={project.status}
          onValueChange={(v) => updateProject.mutate({ id: project.id, data: { status: v as ProjectStatus } })}
        >
          <SelectTrigger className="w-36">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATUSES.map((s) => (
              <SelectItem key={s} value={s}>
                {s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Textarea
        value={notes}
        onChange={(e) => {
          setNotes(e.target.value);
          setDirty(true);
        }}
        rows={3}
        placeholder="Notes…"
      />

      <div className="flex gap-2">
        <Button
          size="sm"
          disabled={!dirty}
          onClick={async () => {
            await updateProject.mutateAsync({ id: project.id, data: { title, notes } });
            setDirty(false);
            toast.success("Project saved");
          }}
        >
          Save
        </Button>
        <Button
          size="sm"
          variant="destructive"
          onClick={async () => {
            await deleteProject.mutateAsync(project.id);
            router.replace("/projects");
          }}
        >
          Delete project
        </Button>
      </div>

      <section className="space-y-2">
        <h2 className="text-sm font-semibold text-muted-foreground">Tasks</h2>
        <QuickAddBox
          defaultFields={{ project_id: project.id }}
          defaultRoleId={project.role_id}
          placeholder="Add a task…"
        />
        <div className="space-y-2">
          {tasks?.map((task) => (
            <TaskCard key={task.id} task={task} onToggleComplete={handleToggleComplete} />
          ))}
        </div>
      </section>
    </div>
  );
}

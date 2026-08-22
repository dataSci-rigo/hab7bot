"use client";

import { useMemo, useState } from "react";
import { format } from "date-fns";
import { toast } from "sonner";
import {
  DndContext,
  type DragEndEvent,
  PointerSensor,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { Button } from "@/components/ui/button";
import { TaskCard } from "@/components/task-card";
import { QuickAddBox } from "@/components/quick-add-box";
import {
  useCompleteTask,
  useMe,
  useRoles,
  useUncompleteTask,
  useUpdateTask,
  useWeekPlan,
} from "@/lib/hooks";
import { TaskStatus, type TaskRead } from "@/lib/api-client";
import { currentIsoWeek, isoWeekDays, shiftIsoWeek } from "@/lib/iso-week";

const BACKLOG_ID = "backlog";

function DraggableTaskCard({
  task,
  onToggleComplete,
  onToggleBigRock,
}: {
  task: TaskRead;
  onToggleComplete: (task: TaskRead) => void;
  onToggleBigRock: (task: TaskRead) => void;
}) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: task.id,
  });
  return (
    <div ref={setNodeRef} className={isDragging ? "opacity-40" : undefined}>
      <TaskCard
        task={task}
        onToggleComplete={onToggleComplete}
        onToggleBigRock={onToggleBigRock}
        dragHandleProps={{ ...attributes, ...listeners }}
      />
    </div>
  );
}

function Column({
  id,
  title,
  tasks,
  onToggleComplete,
  onToggleBigRock,
}: {
  id: string;
  title: string;
  tasks: TaskRead[];
  onToggleComplete: (task: TaskRead) => void;
  onToggleBigRock: (task: TaskRead) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id });
  return (
    <div
      ref={setNodeRef}
      className={`flex w-44 shrink-0 flex-col gap-2 rounded-md border p-2 ${
        isOver ? "bg-accent" : ""
      }`}
    >
      <p className="text-xs font-medium text-muted-foreground">{title}</p>
      <div className="flex flex-col gap-2">
        {tasks.map((task) => (
          <DraggableTaskCard
            key={task.id}
            task={task}
            onToggleComplete={onToggleComplete}
            onToggleBigRock={onToggleBigRock}
          />
        ))}
      </div>
    </div>
  );
}

export default function ThisWeekPage() {
  const [isoWeek, setIsoWeek] = useState(currentIsoWeek());
  const { data: plan, isLoading } = useWeekPlan(isoWeek);
  const { data: roles } = useRoles(true);
  const { data: me } = useMe();
  const updateTask = useUpdateTask();
  const completeTask = useCompleteTask();
  const uncompleteTask = useUncompleteTask();

  // Demo sessions get a staggered entrance so the seeded sample week
  // showcases itself; no-op for the owner.
  const isDemo = me?.role === "guest";
  const riseClass = isDemo ? "demo-rise" : "";
  const riseDelay = (step: number) =>
    isDemo ? { animationDelay: `${step * 130}ms` } : undefined;

  const days = useMemo(() => isoWeekDays(isoWeek), [isoWeek]);

  const roleName = (roleId: string) => roles?.find((r) => r.id === roleId)?.name ?? "—";

  const bigRocksByRole = useMemo(() => {
    const map = new Map<string, TaskRead[]>();
    for (const task of plan?.big_rocks ?? []) {
      const list = map.get(task.role_id) ?? [];
      list.push(task);
      map.set(task.role_id, list);
    }
    return map;
  }, [plan]);

  function tasksForColumn(columnId: string): TaskRead[] {
    if (!plan) return [];
    if (columnId === BACKLOG_ID) {
      return plan.scheduled_tasks.filter((t) => !t.scheduled_day);
    }
    return plan.scheduled_tasks.filter((t) => t.scheduled_day === columnId);
  }

  function handleToggleComplete(task: TaskRead) {
    if (task.status === TaskStatus.DONE) {
      uncompleteTask.mutate(task.id);
    } else {
      completeTask.mutate(task.id);
    }
  }

  function handleToggleBigRock(task: TaskRead) {
    const pinning = !task.is_big_rock;
    if (pinning && (bigRocksByRole.get(task.role_id)?.length ?? 0) >= 3) {
      toast.warning(`${roleName(task.role_id)} already has 3 big rocks this week`);
    }
    updateTask.mutate({ id: task.id, data: { is_big_rock: pinning } });
  }

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 4 } }));

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over) return;
    const taskId = active.id as string;
    const columnId = over.id as string;
    const scheduledDay = columnId === BACKLOG_ID ? null : columnId;
    updateTask.mutate({ id: taskId, data: { scheduled_day: scheduledDay } });
  }

  return (
    <div className="space-y-6">
      <div className={`flex items-center justify-between ${riseClass}`} style={riseDelay(0)}>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setIsoWeek((w) => shiftIsoWeek(w, -1))}>
            ← Prev
          </Button>
          <h1 className="text-lg font-semibold">{isoWeek}</h1>
          <Button variant="outline" size="sm" onClick={() => setIsoWeek((w) => shiftIsoWeek(w, 1))}>
            Next →
          </Button>
        </div>
      </div>

      <div className={riseClass} style={riseDelay(1)}>
        <QuickAddBox
          defaultFields={{ scheduled_week: isoWeek, status: TaskStatus.PLANNED }}
          placeholder="Add a task to this week…"
        />
      </div>

      {bigRocksByRole.size > 0 && (
        <section className={`space-y-2 ${riseClass}`} style={riseDelay(2)}>
          <h2 className="text-sm font-semibold text-muted-foreground">Big Rocks</h2>
          <div className="flex flex-wrap gap-4">
            {[...bigRocksByRole.entries()].map(([roleId, tasks]) => (
              <div key={roleId} className="w-full space-y-2 rounded-md border p-2 sm:w-56">
                <p className="text-xs font-medium">{roleName(roleId)}</p>
                {tasks.map((task) => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    onToggleComplete={handleToggleComplete}
                    onToggleBigRock={handleToggleBigRock}
                  />
                ))}
              </div>
            ))}
          </div>
        </section>
      )}

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
          <div className={`flex gap-3 overflow-x-auto pb-2 ${riseClass}`} style={riseDelay(3)}>
            <Column
              id={BACKLOG_ID}
              title="Backlog"
              tasks={tasksForColumn(BACKLOG_ID)}
              onToggleComplete={handleToggleComplete}
              onToggleBigRock={handleToggleBigRock}
            />
            {days.map((day) => {
              const key = format(day, "yyyy-MM-dd");
              return (
                <Column
                  key={key}
                  id={key}
                  title={format(day, "EEE M/d")}
                  tasks={tasksForColumn(key)}
                  onToggleComplete={handleToggleComplete}
                  onToggleBigRock={handleToggleBigRock}
                />
              );
            })}
          </div>
        </DndContext>
      )}
    </div>
  );
}

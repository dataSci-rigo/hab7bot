import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AuthService,
  CaptureService,
  GoalsService,
  GoogleService,
  InboxService,
  MissionService,
  ProjectsService,
  RolesService,
  SettingsService,
  TasksService,
  WeeksService,
  type AppSettingsUpdate,
  type BreakdownTask,
  type GoalCreate,
  type GoalUpdate,
  type ProjectCreate,
  type ProjectSuggestion,
  type ProjectUpdate,
  type RoleCreate,
  type RoleUpdate,
  type TaskCreate,
  type TaskUpdate,
} from "@/lib/api-client";

// ── auth ─────────────────────────────────────────────────────────────────

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: () => AuthService.meApiV1AuthMeGet(),
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}

// ── roles ────────────────────────────────────────────────────────────────

export function useRoles(activeOnly = false) {
  return useQuery({
    queryKey: ["roles", { activeOnly }],
    queryFn: () => RolesService.listRolesApiV1RolesGet(activeOnly),
  });
}

export function useCreateRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: RoleCreate) => RolesService.createRoleApiV1RolesPost(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["roles"] }),
  });
}

export function useUpdateRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: RoleUpdate }) =>
      RolesService.updateRoleApiV1RolesRoleIdPut(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["roles"] }),
  });
}

export function useDeleteRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => RolesService.deleteRoleApiV1RolesRoleIdDelete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["roles"] }),
  });
}

// ── goals ────────────────────────────────────────────────────────────────

export function useGoals(roleId?: string) {
  return useQuery({
    queryKey: ["goals", { roleId }],
    queryFn: () => GoalsService.listGoalsApiV1GoalsGet(roleId),
  });
}

export function useCreateGoal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: GoalCreate) => GoalsService.createGoalApiV1GoalsPost(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["goals"] }),
  });
}

export function useUpdateGoal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: GoalUpdate }) =>
      GoalsService.updateGoalApiV1GoalsGoalIdPut(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["goals"] }),
  });
}

export function useDeleteGoal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => GoalsService.deleteGoalApiV1GoalsGoalIdDelete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["goals"] }),
  });
}

// ── projects ─────────────────────────────────────────────────────────────

export function useProjects(filters?: { roleId?: string; goalId?: string }) {
  return useQuery({
    queryKey: ["projects", filters ?? {}],
    queryFn: () =>
      ProjectsService.listProjectsApiV1ProjectsGet(
        filters?.roleId,
        filters?.goalId,
      ),
  });
}

export function useProject(id: string | undefined) {
  return useQuery({
    queryKey: ["projects", "detail", id],
    queryFn: () => ProjectsService.getProjectApiV1ProjectsProjectIdGet(id as string),
    enabled: !!id,
  });
}

export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ProjectCreate) => ProjectsService.createProjectApiV1ProjectsPost(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

export function useUpdateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProjectUpdate }) =>
      ProjectsService.updateProjectApiV1ProjectsProjectIdPut(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

export function useDeleteProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => ProjectsService.deleteProjectApiV1ProjectsProjectIdDelete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

// ── tasks ────────────────────────────────────────────────────────────────

export function useTasks(filters?: {
  roleId?: string;
  projectId?: string;
  status?: string;
  scheduledWeek?: string;
}) {
  return useQuery({
    queryKey: ["tasks", filters ?? {}],
    queryFn: () =>
      TasksService.listTasksApiV1TasksGet(
        filters?.roleId,
        filters?.projectId,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        filters?.status as any,
        filters?.scheduledWeek,
      ),
  });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TaskCreate) => TasksService.createTaskApiV1TasksPost(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks"] });
      qc.invalidateQueries({ queryKey: ["week-plan"] });
    },
  });
}

export function useUpdateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TaskUpdate }) =>
      TasksService.updateTaskApiV1TasksTaskIdPut(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks"] });
      qc.invalidateQueries({ queryKey: ["week-plan"] });
    },
  });
}

export function useCompleteTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => TasksService.completeTaskApiV1TasksTaskIdCompletePost(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks"] });
      qc.invalidateQueries({ queryKey: ["week-plan"] });
    },
  });
}

export function useUncompleteTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => TasksService.uncompleteTaskApiV1TasksTaskIdUncompletePost(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks"] });
      qc.invalidateQueries({ queryKey: ["week-plan"] });
    },
  });
}

export function useDeleteTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => TasksService.deleteTaskApiV1TasksTaskIdDelete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks"] });
      qc.invalidateQueries({ queryKey: ["week-plan"] });
    },
  });
}

// ── week plan ────────────────────────────────────────────────────────────

export function useWeekPlan(isoWeek: string) {
  return useQuery({
    queryKey: ["week-plan", isoWeek],
    queryFn: () => WeeksService.getWeekPlanApiV1WeeksIsoWeekPlanGet(isoWeek),
  });
}

export function useSetRoleIntention() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      isoWeek,
      roleId,
      note,
    }: {
      isoWeek: string;
      roleId: string;
      note: string;
    }) =>
      WeeksService.setRoleIntentionApiV1WeeksIsoWeekIntentionsRoleIdPut(isoWeek, roleId, {
        note,
      }),
    onSuccess: (_data, vars) =>
      qc.invalidateQueries({ queryKey: ["week-plan", vars.isoWeek] }),
  });
}

// ── mission ──────────────────────────────────────────────────────────────

export function useMission() {
  return useQuery({
    queryKey: ["mission"],
    queryFn: () => MissionService.getMissionApiV1MissionGet(),
  });
}

export function useUpdateMission() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (content: string) =>
      MissionService.updateMissionApiV1MissionPut({ content }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["mission"] }),
  });
}

// ── settings ─────────────────────────────────────────────────────────────

export function useSettings() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: () => SettingsService.getSettingsApiV1SettingsGet(),
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: AppSettingsUpdate) =>
      SettingsService.updateSettingsApiV1SettingsPut(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings"] }),
  });
}

// ── Google sync ──────────────────────────────────────────────────────────

export function useGoogleStatus() {
  return useQuery({
    queryKey: ["google-status"],
    queryFn: () => GoogleService.getStatusApiV1GoogleStatusGet(),
  });
}

export function useTriggerGoogleSync() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => GoogleService.triggerSyncApiV1GoogleSyncPost(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["google-status"] });
      qc.invalidateQueries({ queryKey: ["tasks"] });
      qc.invalidateQueries({ queryKey: ["week-plan"] });
    },
  });
}

// ── weekly review ────────────────────────────────────────────────────────

export function useWeeklyReview(isoWeek: string) {
  return useQuery({
    queryKey: ["weekly-review", isoWeek],
    queryFn: () => WeeksService.getWeeklyReviewApiV1WeeksIsoWeekReviewGet(isoWeek),
    retry: false,
  });
}

export function useGenerateWeeklyReview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ isoWeek, force }: { isoWeek: string; force?: boolean }) =>
      WeeksService.generateWeeklyReviewApiV1WeeksIsoWeekReviewGeneratePost(isoWeek, force),
    onSuccess: (_data, { isoWeek }) =>
      qc.invalidateQueries({ queryKey: ["weekly-review", isoWeek] }),
  });
}

export function useSaveReflection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ isoWeek, reflection }: { isoWeek: string; reflection: string }) =>
      WeeksService.setWeeklyReviewReflectionApiV1WeeksIsoWeekReviewReflectionPut(isoWeek, {
        reflection,
      }),
    onSuccess: (_data, { isoWeek }) =>
      qc.invalidateQueries({ queryKey: ["weekly-review", isoWeek] }),
  });
}

// ── AI: capture ──────────────────────────────────────────────────────────

export function useCaptureTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (text: string) => CaptureService.captureApiV1CapturePost({ text }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tasks"] });
      qc.invalidateQueries({ queryKey: ["week-plan"] });
    },
  });
}

// ── AI: project breakdown ───────────────────────────────────────────────────

export function useBreakdownProject() {
  return useMutation({
    mutationFn: (projectId: string) =>
      ProjectsService.breakdownProjectApiV1ProjectsProjectIdBreakdownPost(projectId),
  });
}

export function useAcceptBreakdown() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, selected }: { projectId: string; selected: BreakdownTask[] }) =>
      ProjectsService.acceptBreakdownApiV1ProjectsProjectIdBreakdownAcceptPost(projectId, {
        selected,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tasks"] }),
  });
}

// ── AI: project suggestions ─────────────────────────────────────────────────

export function useSuggestProjects() {
  return useMutation({
    mutationFn: () => ProjectsService.suggestProjectsApiV1ProjectsSuggestionsPost(),
  });
}

export function useAcceptSuggestion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (suggestion: ProjectSuggestion) =>
      ProjectsService.acceptSuggestionApiV1ProjectsSuggestionsAcceptPost({ suggestion }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["projects"] }),
  });
}

// ── AI: inbox triage ─────────────────────────────────────────────────────────

export function useInboxAiTriage() {
  return useMutation({
    mutationFn: () => InboxService.aiTriageApiV1InboxAiTriagePost(),
  });
}

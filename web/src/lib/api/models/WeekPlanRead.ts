/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RoleIntentionRead } from './RoleIntentionRead';
import type { TaskRead } from './TaskRead';
export type WeekPlanRead = {
    iso_week: string;
    big_rocks: Array<TaskRead>;
    scheduled_tasks: Array<TaskRead>;
    role_intentions: Array<RoleIntentionRead>;
};


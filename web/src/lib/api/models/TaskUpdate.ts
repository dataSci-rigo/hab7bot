/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Quadrant } from './Quadrant';
import type { TaskStatus } from './TaskStatus';
export type TaskUpdate = {
    title?: (string | null);
    notes?: (string | null);
    role_id?: (string | null);
    project_id?: (string | null);
    quadrant?: (Quadrant | null);
    is_big_rock?: (boolean | null);
    status?: (TaskStatus | null);
    scheduled_week?: (string | null);
    scheduled_day?: (string | null);
    estimate_minutes?: (number | null);
    actual_minutes?: (number | null);
};


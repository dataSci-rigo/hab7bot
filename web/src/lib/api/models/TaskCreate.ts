/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Quadrant } from './Quadrant';
import type { TaskOrigin } from './TaskOrigin';
import type { TaskStatus } from './TaskStatus';
export type TaskCreate = {
    title: string;
    notes?: (string | null);
    role_id: string;
    project_id?: (string | null);
    quadrant?: Quadrant;
    is_big_rock?: boolean;
    status?: TaskStatus;
    scheduled_week?: (string | null);
    scheduled_day?: (string | null);
    estimate_minutes?: (number | null);
    origin?: TaskOrigin;
};


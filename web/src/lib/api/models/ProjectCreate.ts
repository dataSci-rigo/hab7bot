/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ProjectOrigin } from './ProjectOrigin';
import type { ProjectStatus } from './ProjectStatus';
export type ProjectCreate = {
    role_id: string;
    goal_id?: (string | null);
    title: string;
    notes?: (string | null);
    status?: ProjectStatus;
    origin?: ProjectOrigin;
};


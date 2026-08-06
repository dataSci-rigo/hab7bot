/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Quadrant } from './Quadrant';
export type InboxTriageSuggestion = {
    task_id: string;
    role_id: (string | null);
    role_name: (string | null);
    quadrant: Quadrant;
    is_big_rock_candidate: boolean;
    project_id: (string | null);
    project_title: (string | null);
};


/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Quadrant } from './Quadrant';
export type BreakdownTask = {
    title: string;
    estimate_minutes?: (number | null);
    quadrant?: Quadrant;
    /**
     * 0 = this week, 1 = next week, etc.
     */
    suggested_week_offset?: number;
};


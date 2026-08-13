/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ReflectionUpdate } from '../models/ReflectionUpdate';
import type { RoleIntentionSet } from '../models/RoleIntentionSet';
import type { WeeklyReviewRead } from '../models/WeeklyReviewRead';
import type { WeekPlanRead } from '../models/WeekPlanRead';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class WeeksService {
    /**
     * Get Week Plan
     * @param isoWeek
     * @returns WeekPlanRead Successful Response
     * @throws ApiError
     */
    public static getWeekPlanApiV1WeeksIsoWeekPlanGet(
        isoWeek: string,
    ): CancelablePromise<WeekPlanRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/weeks/{iso_week}/plan',
            path: {
                'iso_week': isoWeek,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Set Role Intention
     * @param isoWeek
     * @param roleId
     * @param requestBody
     * @returns boolean Successful Response
     * @throws ApiError
     */
    public static setRoleIntentionApiV1WeeksIsoWeekIntentionsRoleIdPut(
        isoWeek: string,
        roleId: string,
        requestBody: RoleIntentionSet,
    ): CancelablePromise<Record<string, boolean>> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/weeks/{iso_week}/intentions/{role_id}',
            path: {
                'iso_week': isoWeek,
                'role_id': roleId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Weekly Review
     * @param isoWeek
     * @returns WeeklyReviewRead Successful Response
     * @throws ApiError
     */
    public static getWeeklyReviewApiV1WeeksIsoWeekReviewGet(
        isoWeek: string,
    ): CancelablePromise<WeeklyReviewRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/weeks/{iso_week}/review',
            path: {
                'iso_week': isoWeek,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Generate Weekly Review
     * @param isoWeek
     * @param force
     * @returns WeeklyReviewRead Successful Response
     * @throws ApiError
     */
    public static generateWeeklyReviewApiV1WeeksIsoWeekReviewGeneratePost(
        isoWeek: string,
        force: boolean = false,
    ): CancelablePromise<WeeklyReviewRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/weeks/{iso_week}/review/generate',
            path: {
                'iso_week': isoWeek,
            },
            query: {
                'force': force,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Set Weekly Review Reflection
     * @param isoWeek
     * @param requestBody
     * @returns WeeklyReviewRead Successful Response
     * @throws ApiError
     */
    public static setWeeklyReviewReflectionApiV1WeeksIsoWeekReviewReflectionPut(
        isoWeek: string,
        requestBody: ReflectionUpdate,
    ): CancelablePromise<WeeklyReviewRead> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/weeks/{iso_week}/review/reflection',
            path: {
                'iso_week': isoWeek,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}

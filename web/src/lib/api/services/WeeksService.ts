/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RoleIntentionSet } from '../models/RoleIntentionSet';
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
}

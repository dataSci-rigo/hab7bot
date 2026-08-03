/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GoalCreate } from '../models/GoalCreate';
import type { GoalRead } from '../models/GoalRead';
import type { GoalUpdate } from '../models/GoalUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class GoalsService {
    /**
     * List Goals
     * @param roleId
     * @returns GoalRead Successful Response
     * @throws ApiError
     */
    public static listGoalsApiV1GoalsGet(
        roleId?: (string | null),
    ): CancelablePromise<Array<GoalRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/goals',
            query: {
                'role_id': roleId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Goal
     * @param requestBody
     * @returns GoalRead Successful Response
     * @throws ApiError
     */
    public static createGoalApiV1GoalsPost(
        requestBody: GoalCreate,
    ): CancelablePromise<GoalRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/goals',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Goal
     * @param goalId
     * @returns GoalRead Successful Response
     * @throws ApiError
     */
    public static getGoalApiV1GoalsGoalIdGet(
        goalId: string,
    ): CancelablePromise<GoalRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/goals/{goal_id}',
            path: {
                'goal_id': goalId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Goal
     * @param goalId
     * @param requestBody
     * @returns GoalRead Successful Response
     * @throws ApiError
     */
    public static updateGoalApiV1GoalsGoalIdPut(
        goalId: string,
        requestBody: GoalUpdate,
    ): CancelablePromise<GoalRead> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/goals/{goal_id}',
            path: {
                'goal_id': goalId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Goal
     * @param goalId
     * @returns void
     * @throws ApiError
     */
    public static deleteGoalApiV1GoalsGoalIdDelete(
        goalId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/goals/{goal_id}',
            path: {
                'goal_id': goalId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}

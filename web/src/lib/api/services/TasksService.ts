/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TaskCreate } from '../models/TaskCreate';
import type { TaskRead } from '../models/TaskRead';
import type { TaskStatus } from '../models/TaskStatus';
import type { TaskUpdate } from '../models/TaskUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class TasksService {
    /**
     * List Tasks
     * @param roleId
     * @param projectId
     * @param status
     * @param scheduledWeek
     * @returns TaskRead Successful Response
     * @throws ApiError
     */
    public static listTasksApiV1TasksGet(
        roleId?: (string | null),
        projectId?: (string | null),
        status?: (TaskStatus | null),
        scheduledWeek?: (string | null),
    ): CancelablePromise<Array<TaskRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/tasks',
            query: {
                'role_id': roleId,
                'project_id': projectId,
                'status': status,
                'scheduled_week': scheduledWeek,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Task
     * @param requestBody
     * @returns TaskRead Successful Response
     * @throws ApiError
     */
    public static createTaskApiV1TasksPost(
        requestBody: TaskCreate,
    ): CancelablePromise<TaskRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/tasks',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Task
     * @param taskId
     * @returns TaskRead Successful Response
     * @throws ApiError
     */
    public static getTaskApiV1TasksTaskIdGet(
        taskId: string,
    ): CancelablePromise<TaskRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/tasks/{task_id}',
            path: {
                'task_id': taskId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Task
     * @param taskId
     * @param requestBody
     * @returns TaskRead Successful Response
     * @throws ApiError
     */
    public static updateTaskApiV1TasksTaskIdPut(
        taskId: string,
        requestBody: TaskUpdate,
    ): CancelablePromise<TaskRead> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/tasks/{task_id}',
            path: {
                'task_id': taskId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Task
     * @param taskId
     * @returns void
     * @throws ApiError
     */
    public static deleteTaskApiV1TasksTaskIdDelete(
        taskId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/tasks/{task_id}',
            path: {
                'task_id': taskId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Complete Task
     * @param taskId
     * @returns TaskRead Successful Response
     * @throws ApiError
     */
    public static completeTaskApiV1TasksTaskIdCompletePost(
        taskId: string,
    ): CancelablePromise<TaskRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/tasks/{task_id}/complete',
            path: {
                'task_id': taskId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Uncomplete Task
     * @param taskId
     * @returns TaskRead Successful Response
     * @throws ApiError
     */
    public static uncompleteTaskApiV1TasksTaskIdUncompletePost(
        taskId: string,
    ): CancelablePromise<TaskRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/tasks/{task_id}/uncomplete',
            path: {
                'task_id': taskId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}

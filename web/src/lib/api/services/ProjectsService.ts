/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BreakdownAcceptRequest } from '../models/BreakdownAcceptRequest';
import type { BreakdownProposal } from '../models/BreakdownProposal';
import type { ProjectCreate } from '../models/ProjectCreate';
import type { ProjectRead } from '../models/ProjectRead';
import type { ProjectStatus } from '../models/ProjectStatus';
import type { ProjectSuggestion } from '../models/ProjectSuggestion';
import type { ProjectUpdate } from '../models/ProjectUpdate';
import type { SuggestionAcceptRequest } from '../models/SuggestionAcceptRequest';
import type { TaskRead } from '../models/TaskRead';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ProjectsService {
    /**
     * List Projects
     * @param roleId
     * @param goalId
     * @param status
     * @returns ProjectRead Successful Response
     * @throws ApiError
     */
    public static listProjectsApiV1ProjectsGet(
        roleId?: (string | null),
        goalId?: (string | null),
        status?: (ProjectStatus | null),
    ): CancelablePromise<Array<ProjectRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/projects',
            query: {
                'role_id': roleId,
                'goal_id': goalId,
                'status': status,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Project
     * @param requestBody
     * @returns ProjectRead Successful Response
     * @throws ApiError
     */
    public static createProjectApiV1ProjectsPost(
        requestBody: ProjectCreate,
    ): CancelablePromise<ProjectRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/projects',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Project
     * @param projectId
     * @returns ProjectRead Successful Response
     * @throws ApiError
     */
    public static getProjectApiV1ProjectsProjectIdGet(
        projectId: string,
    ): CancelablePromise<ProjectRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/projects/{project_id}',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Project
     * @param projectId
     * @param requestBody
     * @returns ProjectRead Successful Response
     * @throws ApiError
     */
    public static updateProjectApiV1ProjectsProjectIdPut(
        projectId: string,
        requestBody: ProjectUpdate,
    ): CancelablePromise<ProjectRead> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/projects/{project_id}',
            path: {
                'project_id': projectId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Project
     * @param projectId
     * @returns void
     * @throws ApiError
     */
    public static deleteProjectApiV1ProjectsProjectIdDelete(
        projectId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/projects/{project_id}',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Suggest Projects
     * @returns ProjectSuggestion Successful Response
     * @throws ApiError
     */
    public static suggestProjectsApiV1ProjectsSuggestionsPost(): CancelablePromise<Array<ProjectSuggestion>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/projects/suggestions',
        });
    }
    /**
     * Accept Suggestion
     * @param requestBody
     * @returns ProjectRead Successful Response
     * @throws ApiError
     */
    public static acceptSuggestionApiV1ProjectsSuggestionsAcceptPost(
        requestBody: SuggestionAcceptRequest,
    ): CancelablePromise<ProjectRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/projects/suggestions/accept',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Breakdown Project
     * @param projectId
     * @returns BreakdownProposal Successful Response
     * @throws ApiError
     */
    public static breakdownProjectApiV1ProjectsProjectIdBreakdownPost(
        projectId: string,
    ): CancelablePromise<BreakdownProposal> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/projects/{project_id}/breakdown',
            path: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Accept Breakdown
     * @param projectId
     * @param requestBody
     * @returns TaskRead Successful Response
     * @throws ApiError
     */
    public static acceptBreakdownApiV1ProjectsProjectIdBreakdownAcceptPost(
        projectId: string,
        requestBody: BreakdownAcceptRequest,
    ): CancelablePromise<Array<TaskRead>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/projects/{project_id}/breakdown/accept',
            path: {
                'project_id': projectId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}

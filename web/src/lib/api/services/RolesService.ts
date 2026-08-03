/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RoleCreate } from '../models/RoleCreate';
import type { RoleRead } from '../models/RoleRead';
import type { RoleUpdate } from '../models/RoleUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class RolesService {
    /**
     * List Roles
     * @param activeOnly
     * @returns RoleRead Successful Response
     * @throws ApiError
     */
    public static listRolesApiV1RolesGet(
        activeOnly: boolean = false,
    ): CancelablePromise<Array<RoleRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/roles',
            query: {
                'active_only': activeOnly,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Role
     * @param requestBody
     * @returns RoleRead Successful Response
     * @throws ApiError
     */
    public static createRoleApiV1RolesPost(
        requestBody: RoleCreate,
    ): CancelablePromise<RoleRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/roles',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Role
     * @param roleId
     * @returns RoleRead Successful Response
     * @throws ApiError
     */
    public static getRoleApiV1RolesRoleIdGet(
        roleId: string,
    ): CancelablePromise<RoleRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/roles/{role_id}',
            path: {
                'role_id': roleId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Role
     * @param roleId
     * @param requestBody
     * @returns RoleRead Successful Response
     * @throws ApiError
     */
    public static updateRoleApiV1RolesRoleIdPut(
        roleId: string,
        requestBody: RoleUpdate,
    ): CancelablePromise<RoleRead> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/roles/{role_id}',
            path: {
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
     * Delete Role
     * @param roleId
     * @returns void
     * @throws ApiError
     */
    public static deleteRoleApiV1RolesRoleIdDelete(
        roleId: string,
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/roles/{role_id}',
            path: {
                'role_id': roleId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}

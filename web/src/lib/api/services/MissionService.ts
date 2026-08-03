/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { MissionRead } from '../models/MissionRead';
import type { MissionUpdate } from '../models/MissionUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class MissionService {
    /**
     * Get Mission
     * @returns MissionRead Successful Response
     * @throws ApiError
     */
    public static getMissionApiV1MissionGet(): CancelablePromise<MissionRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/mission',
        });
    }
    /**
     * Update Mission
     * @param requestBody
     * @returns MissionRead Successful Response
     * @throws ApiError
     */
    public static updateMissionApiV1MissionPut(
        requestBody: MissionUpdate,
    ): CancelablePromise<MissionRead> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/mission',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}

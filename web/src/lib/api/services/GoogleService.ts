/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GoogleStatus } from '../models/GoogleStatus';
import type { GoogleSyncResult } from '../models/GoogleSyncResult';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class GoogleService {
    /**
     * Get Status
     * @returns GoogleStatus Successful Response
     * @throws ApiError
     */
    public static getStatusApiV1GoogleStatusGet(): CancelablePromise<GoogleStatus> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/google/status',
        });
    }
    /**
     * Trigger Sync
     * @returns GoogleSyncResult Successful Response
     * @throws ApiError
     */
    public static triggerSyncApiV1GoogleSyncPost(): CancelablePromise<GoogleSyncResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/google/sync',
        });
    }
}

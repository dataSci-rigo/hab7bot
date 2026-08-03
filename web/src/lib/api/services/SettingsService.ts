/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AppSettingsRead } from '../models/AppSettingsRead';
import type { AppSettingsUpdate } from '../models/AppSettingsUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class SettingsService {
    /**
     * Get Settings
     * @returns AppSettingsRead Successful Response
     * @throws ApiError
     */
    public static getSettingsApiV1SettingsGet(): CancelablePromise<AppSettingsRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/settings',
        });
    }
    /**
     * Update Settings
     * @param requestBody
     * @returns AppSettingsRead Successful Response
     * @throws ApiError
     */
    public static updateSettingsApiV1SettingsPut(
        requestBody: AppSettingsUpdate,
    ): CancelablePromise<AppSettingsRead> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/settings',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}

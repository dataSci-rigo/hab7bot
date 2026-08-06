/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CaptureRequest } from '../models/CaptureRequest';
import type { TaskRead } from '../models/TaskRead';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class CaptureService {
    /**
     * Capture
     * @param requestBody
     * @returns TaskRead Successful Response
     * @throws ApiError
     */
    public static captureApiV1CapturePost(
        requestBody: CaptureRequest,
    ): CancelablePromise<TaskRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/capture',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}

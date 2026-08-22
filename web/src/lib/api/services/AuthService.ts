/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LoginRequest } from '../models/LoginRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AuthService {
    /**
     * Login
     * One form, two passwords: the owner's APP_PASSWORD, or the openly
     * hinted demo password ("demo" by default) which starts a read-only
     * session served from the seeded showcase database (scripts/seed_demo.py)
     * — never the real planner. Owner match is checked first so the demo
     * password can never shadow it.
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static loginApiV1AuthLoginPost(
        requestBody: LoginRequest,
    ): CancelablePromise<Record<string, (boolean | string)>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/auth/login',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Logout
     * @returns boolean Successful Response
     * @throws ApiError
     */
    public static logoutApiV1AuthLogoutPost(): CancelablePromise<Record<string, boolean>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/auth/logout',
        });
    }
    /**
     * Me
     * @returns any Successful Response
     * @throws ApiError
     */
    public static meApiV1AuthMeGet(): CancelablePromise<Record<string, (boolean | string)>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/auth/me',
        });
    }
}

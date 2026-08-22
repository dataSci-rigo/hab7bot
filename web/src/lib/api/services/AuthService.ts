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
     * Username + password. Reserved usernames: "owner" (APP_PASSWORD, the
     * real planner) and "demo" (DEMO_PASSWORD, the openly hinted read-only
     * showcase — see scripts/seed_demo.py). Any other username is looked up in
     * HAB7BOT_ACCOUNTS and gets that member's own private database.
     * parse_accounts warns loudly about password collisions across logins.
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

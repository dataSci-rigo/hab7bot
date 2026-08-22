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
     * One form, one password box — the password IS the identity:
     * APP_PASSWORD → owner (real planner); the openly hinted demo password →
     * read-only guest served from the seeded showcase DB; an HAB7BOT_ACCOUNTS
     * password → that member's own private database. Owner is matched first so
     * nothing can shadow it; parse_accounts warns about duplicate passwords.
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

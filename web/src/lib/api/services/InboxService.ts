/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { InboxTriageSuggestion } from '../models/InboxTriageSuggestion';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class InboxService {
    /**
     * Ai Triage
     * @returns InboxTriageSuggestion Successful Response
     * @throws ApiError
     */
    public static aiTriageApiV1InboxAiTriagePost(): CancelablePromise<Array<InboxTriageSuggestion>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/inbox/ai-triage',
        });
    }
}

/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type CaptureRequest = {
    text: string;
    origin?: CaptureRequest.origin;
};
export namespace CaptureRequest {
    export enum origin {
        WEB = 'web',
        BRAINDUMP = 'braindump',
    }
}


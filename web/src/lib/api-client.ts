import { OpenAPI } from "@/lib/api";

OpenAPI.BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
OpenAPI.WITH_CREDENTIALS = true;
OpenAPI.CREDENTIALS = "include";

export * from "@/lib/api";

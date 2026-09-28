/**
 * Settings → teacher HTTP client. Domain traffic is loopback HTTP only
 * (never Electron IPC as a domain bus); `base_url` + `bearer` come from the
 * preload lifecycle bridge. Never silently succeeds against a dead/unreachable
 * teacher — every failure surfaces a shaped `TeacherApiError` for the caller
 * to render as error + retry.
 */

export interface TeacherAuth {
  state: "starting" | "running" | "stopped" | "error";
  base_url: string;
  bearer: string | null;
  message?: string;
}

export interface LlmConfigStatus {
  configured: boolean;
}

const UNAVAILABLE_AUTH: TeacherAuth = {
  state: "error",
  base_url: "",
  bearer: null,
  message: "Хост учителя недоступен (preload не подключён)",
};

export class TeacherApiError extends Error {
  readonly code: string;
  readonly retryable: boolean;
  readonly status: number;

  constructor(
    code: string,
    message: string,
    retryable: boolean,
    status: number,
  ) {
    super(message);
    this.code = code;
    this.retryable = retryable;
    this.status = status;
  }
}

function hasTeacherBridge(): boolean {
  return typeof window !== "undefined" && typeof window.teacher !== "undefined";
}

export async function getTeacherAuth(): Promise<TeacherAuth> {
  if (!hasTeacherBridge()) {
    return { ...UNAVAILABLE_AUTH };
  }
  return window.teacher.getAuth();
}

export async function retryTeacher(): Promise<TeacherAuth> {
  if (!hasTeacherBridge()) {
    return { ...UNAVAILABLE_AUTH };
  }
  return window.teacher.retry();
}

async function parseSuccessJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch {
    throw new TeacherApiError(
      "invalid_response",
      "Некорректный ответ учителя",
      true,
      response.status,
    );
  }
}

async function toApiError(response: Response): Promise<TeacherApiError> {
  try {
    const body = (await response.json()) as {
      code?: string;
      message?: string;
      retryable?: boolean;
    };
    return new TeacherApiError(
      body.code ?? "http_error",
      body.message ?? "Request failed",
      Boolean(body.retryable),
      response.status,
    );
  } catch {
    return new TeacherApiError(
      "network_error",
      "Network error",
      true,
      response.status,
    );
  }
}

function requireRunningAuth(auth: TeacherAuth): void {
  if (auth.state !== "running" || !auth.bearer || !auth.base_url) {
    throw new TeacherApiError(
      "teacher_unavailable",
      "Учитель не запущен",
      true,
      0,
    );
  }
}

async function authorizedFetch(
  auth: TeacherAuth,
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  requireRunningAuth(auth);
  const timeoutMs = 8000;
  try {
    return await fetch(`${auth.base_url}${path}`, {
      ...init,
      signal: init.signal ?? AbortSignal.timeout(timeoutMs),
      headers: {
        ...init.headers,
        Authorization: `Bearer ${auth.bearer}`,
      },
    });
  } catch (err) {
    if (
      err instanceof DOMException &&
      (err.name === "TimeoutError" || err.name === "AbortError")
    ) {
      throw new TeacherApiError(
        "timeout",
        "Учитель не ответил вовремя",
        true,
        0,
      );
    }
    throw new TeacherApiError("network_error", "Нет связи с учителем", true, 0);
  }
}

export async function fetchLlmConfigStatus(
  auth: TeacherAuth,
): Promise<LlmConfigStatus> {
  const response = await authorizedFetch(auth, "/config/llm");
  if (!response.ok) {
    throw await toApiError(response);
  }
  return parseSuccessJson<LlmConfigStatus>(response);
}

export async function saveLlmApiKey(
  auth: TeacherAuth,
  llmApiKey: string,
): Promise<LlmConfigStatus> {
  const response = await authorizedFetch(auth, "/config/llm", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ llm_api_key: llmApiKey }),
  });
  if (!response.ok) {
    throw await toApiError(response);
  }
  return parseSuccessJson<LlmConfigStatus>(response);
}

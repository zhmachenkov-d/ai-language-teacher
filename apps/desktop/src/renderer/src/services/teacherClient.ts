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

export interface WeeklySlot {
  weekday: number;
  start_minute: number;
}

export type IntakeStep =
  | "greeting"
  | "goals"
  | "interests"
  | "duration"
  | "schedule"
  | "complete";

export type PlacementStage =
  | "briefing"
  | "written"
  | "listening"
  | "speaking"
  | "complete";

/** Client-safe item projection — `correct_index` never leaves the server. */
export interface PlacementChoiceItemPublic {
  prompt: string;
  options: string[];
}

export interface PlacementItemsPublic {
  written: PlacementChoiceItemPublic[];
  listening: { questions: PlacementChoiceItemPublic[] };
  speaking_prompts: string[];
}

export interface LearnerProfile {
  id: string;
  target_language: string;
  l1: string;
  timezone: string;
  address_as: string | null;
  age: number | null;
  goals: string[];
  desired_outcome: string[];
  interests: string[];
  emphasis: string[];
  lesson_duration_minutes: number | null;
  weekly_slots: WeeklySlot[];
  intake_step: IntakeStep;
  consent_mic: boolean;
  consent_telegram: boolean;
  consent_ai: boolean;
  consent_privacy: boolean;
  consent_complete: boolean;
  placement_stage: PlacementStage;
  placement_items: PlacementItemsPublic | null;
  placement_written_answers: number[];
  placement_written_score: number | null;
  placement_listening_generated: boolean;
  placement_listening_played: boolean;
  placement_listening_answers: number[];
  placement_listening_score: number | null;
  placement_speaking_transcript: string | null;
  placement_speaking_score: number | null;
  placement_complete: boolean;
  plan_complete: boolean;
}

export type LearnerPatch = Partial<{
  address_as: string;
  age: number;
  goals: string[];
  desired_outcome: string[];
  interests: string[];
  emphasis: string[];
  lesson_duration_minutes: number;
  timezone: string;
  weekly_slots: WeeklySlot[];
  intake_step: IntakeStep;
  consent_mic: boolean;
  consent_telegram: boolean;
  consent_ai: boolean;
  consent_privacy: boolean;
  consent_complete: boolean;
  placement_stage: PlacementStage;
  placement_written_answers: number[];
  placement_listening_played: boolean;
  placement_listening_answers: number[];
  placement_complete: boolean;
}>;

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

export async function fetchLearner(auth: TeacherAuth): Promise<LearnerProfile> {
  const response = await authorizedFetch(auth, "/learner");
  if (!response.ok) {
    throw await toApiError(response);
  }
  return parseSuccessJson<LearnerProfile>(response);
}

export async function patchLearner(
  auth: TeacherAuth,
  body: LearnerPatch,
): Promise<LearnerProfile> {
  const response = await authorizedFetch(auth, "/learner", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw await toApiError(response);
  }
  return parseSuccessJson<LearnerProfile>(response);
}

/**
 * Generate (or fetch the already-cached) one-per-run placement item set.
 * 422 `llm_config_missing` / `llm_generation_failed` are retryable — the
 * caller must show a Settings path + retry, never fabricate items.
 */
export async function generatePlacementItems(
  auth: TeacherAuth,
): Promise<PlacementItemsPublic> {
  const response = await authorizedFetch(auth, "/placement/items", {
    method: "POST",
  });
  if (!response.ok) {
    throw await toApiError(response);
  }
  return parseSuccessJson<PlacementItemsPublic>(response);
}

export interface ListeningAudio {
  audio_base64: string;
  mime_type: string;
}

/** Synthesize the listening script via local TTS. 422 `voice_unavailable` is retryable. */
export async function synthesizeListeningAudio(
  auth: TeacherAuth,
): Promise<ListeningAudio> {
  const response = await authorizedFetch(auth, "/placement/listening/audio", {
    method: "POST",
  });
  if (!response.ok) {
    throw await toApiError(response);
  }
  return parseSuccessJson<ListeningAudio>(response);
}

/**
 * Transcribe a local mic capture via local STT and persist transcript+score.
 * 422 `voice_unavailable` is retryable — no fake transcript/pass on failure.
 */
export async function transcribeSpeakingAudio(
  auth: TeacherAuth,
  body: { audio_base64: string; mime_type: string },
): Promise<LearnerProfile> {
  const response = await authorizedFetch(auth, "/placement/speaking/transcribe", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw await toApiError(response);
  }
  return parseSuccessJson<LearnerProfile>(response);
}

export interface PathOption {
  id: string;
  title: string;
  summary: string;
  recommended: boolean;
}

export interface LivingPlanLesson {
  id: string;
  scheduled_at: string;
  timezone: string;
}

export interface LivingPlanProjection {
  id: string;
  goals: string[];
  focus: string;
  upcoming_topics: string[];
  difficulty: string;
  selected_path_id: string;
  proposed_paths: PathOption[];
  revisable: boolean;
  target_language: string;
  l1: string;
  lessons: LivingPlanLesson[];
}

/**
 * Create (or return the existing) Living plan after placement.
 * POST body must be `{}`. Idempotent when a plan already exists (no re-LLM).
 * 422: llm_config_missing | llm_generation_failed | placement_incomplete |
 * placement_scores_missing | schedule_unusable.
 */
export async function createLivingPlan(
  auth: TeacherAuth,
): Promise<LivingPlanProjection> {
  // LLM propose can take up to ~30s; override the default 8s fetch timeout.
  const response = await authorizedFetch(auth, "/living-plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
    signal: AbortSignal.timeout(35000),
  });
  if (!response.ok) {
    throw await toApiError(response);
  }
  return parseSuccessJson<LivingPlanProjection>(response);
}

/** Fetch the Living plan. 404 when !plan_complete; 500 if FLAG without row. */
export async function fetchLivingPlan(
  auth: TeacherAuth,
): Promise<LivingPlanProjection> {
  const response = await authorizedFetch(auth, "/living-plan");
  if (!response.ok) {
    throw await toApiError(response);
  }
  return parseSuccessJson<LivingPlanProjection>(response);
}

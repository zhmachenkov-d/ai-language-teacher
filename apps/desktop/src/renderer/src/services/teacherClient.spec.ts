import { afterEach, describe, expect, it, vi } from "vitest";
import {
  createLivingPlan,
  fetchLearner,
  fetchLivingPlan,
  fetchLlmConfigStatus,
  generatePlacementItems,
  getTeacherAuth,
  patchLearner,
  saveLlmApiKey,
  synthesizeListeningAudio,
  TeacherApiError,
  transcribeSpeakingAudio,
  type TeacherAuth,
} from "./teacherClient";

const RUNNING: TeacherAuth = {
  state: "running",
  base_url: "http://127.0.0.1:8765",
  bearer: "tok-123",
};

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("teacherClient", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    // Restore whatever preload bridge the global test-setup installs.
    Object.defineProperty(window, "teacher", {
      configurable: true,
      value: {
        getAuth: vi.fn().mockResolvedValue(RUNNING),
        retry: vi.fn().mockResolvedValue(RUNNING),
        onStatusChange: vi.fn().mockReturnValue(() => undefined),
      },
    });
  });

  it("getTeacherAuth reports an error state when the preload bridge is missing", async () => {
    // @ts-expect-error - simulate a missing preload bridge
    delete window.teacher;
    const auth = await getTeacherAuth();
    expect(auth.state).toBe("error");
  });

  it("fetchLlmConfigStatus sends Bearer auth and parses configured status", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, { configured: true }));
    vi.stubGlobal("fetch", fetchMock);
    const status = await fetchLlmConfigStatus(RUNNING);
    expect(status).toEqual({ configured: true });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8765/config/llm",
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer tok-123" }),
      }),
    );
  });

  it("surfaces a shaped TeacherApiError on non-2xx without throwing raw fetch errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          jsonResponse(401, {
            code: "unauthorized",
            message: "no",
            retryable: false,
          }),
        ),
    );
    await expect(fetchLlmConfigStatus(RUNNING)).rejects.toMatchObject({
      code: "unauthorized",
      retryable: false,
      status: 401,
    });
  });

  it("rejects with teacher_unavailable when auth state is not running (no silent call)", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const stopped: TeacherAuth = {
      state: "stopped",
      base_url: "",
      bearer: null,
    };
    await expect(fetchLlmConfigStatus(stopped)).rejects.toBeInstanceOf(
      TeacherApiError,
    );
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("saveLlmApiKey PUTs snake_case body and returns configured status", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, { configured: true }));
    vi.stubGlobal("fetch", fetchMock);
    const status = await saveLlmApiKey(RUNNING, "sk-abc");
    expect(status).toEqual({ configured: true });
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.method).toBe("PUT");
    expect(init.body).toBe(JSON.stringify({ llm_api_key: "sk-abc" }));
  });

  it("wraps a network failure as a retryable TeacherApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("ECONNREFUSED")),
    );
    await expect(saveLlmApiKey(RUNNING, "sk-abc")).rejects.toMatchObject({
      code: "network_error",
      retryable: true,
    });
  });

  it("wraps AbortSignal timeout as a retryable timeout TeacherApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockRejectedValue(
          new DOMException("The operation was aborted", "TimeoutError"),
        ),
    );
    await expect(saveLlmApiKey(RUNNING, "sk-abc")).rejects.toMatchObject({
      code: "timeout",
      retryable: true,
    });
  });

  it("fetchLearner GETs /learner with Bearer auth", async () => {
    const profile = {
      id: "abc",
      target_language: "en",
      l1: "ru",
      timezone: "UTC",
      address_as: null,
      age: null,
      goals: [],
      desired_outcome: [],
      interests: [],
      emphasis: [],
      lesson_duration_minutes: null,
      weekly_slots: [],
      intake_step: "greeting",
      consent_mic: false,
      consent_telegram: false,
      consent_ai: false,
      consent_privacy: false,
      consent_complete: false,
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, profile));
    vi.stubGlobal("fetch", fetchMock);
    await expect(fetchLearner(RUNNING)).resolves.toEqual(profile);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8765/learner",
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer tok-123" }),
      }),
    );
  });

  it("patchLearner PATCHes snake_case body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        id: "abc",
        target_language: "en",
        l1: "ru",
        timezone: "UTC",
        address_as: "Алекс",
        age: 28,
        goals: [],
        desired_outcome: [],
        interests: [],
        emphasis: [],
        lesson_duration_minutes: null,
        weekly_slots: [],
        intake_step: "goals",
        consent_mic: false,
        consent_telegram: false,
        consent_ai: false,
        consent_privacy: false,
        consent_complete: false,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    await patchLearner(RUNNING, {
      address_as: "Алекс",
      age: 28,
      intake_step: "goals",
    });
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.method).toBe("PATCH");
    expect(init.body).toBe(
      JSON.stringify({
        address_as: "Алекс",
        age: 28,
        intake_step: "goals",
      }),
    );
  });

  it("generatePlacementItems POSTs and returns the public item set", async () => {
    const items = {
      written: [{ prompt: "Q", options: ["a", "b", "c"] }],
      listening: { questions: [{ prompt: "L", options: ["a", "b"] }] },
      speaking_prompts: ["Tell me about your day."],
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, items));
    vi.stubGlobal("fetch", fetchMock);
    await expect(generatePlacementItems(RUNNING)).resolves.toEqual(items);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://127.0.0.1:8765/placement/items");
    expect(init.method).toBe("POST");
  });

  it("generatePlacementItems surfaces llm_config_missing as retryable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(422, {
          code: "llm_config_missing",
          message: "LLM API key is not configured",
          retryable: true,
        }),
      ),
    );
    await expect(generatePlacementItems(RUNNING)).rejects.toMatchObject({
      code: "llm_config_missing",
      retryable: true,
    });
  });

  it("synthesizeListeningAudio POSTs and returns base64 audio", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        jsonResponse(200, { audio_base64: "abc123", mime_type: "audio/wav" }),
      );
    vi.stubGlobal("fetch", fetchMock);
    await expect(synthesizeListeningAudio(RUNNING)).resolves.toEqual({
      audio_base64: "abc123",
      mime_type: "audio/wav",
    });
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://127.0.0.1:8765/placement/listening/audio");
    expect(init.method).toBe("POST");
  });

  it("synthesizeListeningAudio surfaces voice_unavailable as retryable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(422, {
          code: "voice_unavailable",
          message: "local TTS engine not found",
          retryable: true,
        }),
      ),
    );
    await expect(synthesizeListeningAudio(RUNNING)).rejects.toMatchObject({
      code: "voice_unavailable",
      retryable: true,
    });
  });

  it("transcribeSpeakingAudio POSTs base64 audio and resolves to the updated learner", async () => {
    const learner = {
      id: "abc",
      placement_speaking_transcript: "hello world",
      placement_speaking_score: 0.5,
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, learner));
    vi.stubGlobal("fetch", fetchMock);
    await expect(
      transcribeSpeakingAudio(RUNNING, {
        audio_base64: "abc",
        mime_type: "audio/webm",
      }),
    ).resolves.toEqual(learner);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://127.0.0.1:8765/placement/speaking/transcribe");
    expect(init.method).toBe("POST");
    expect(init.body).toBe(
      JSON.stringify({ audio_base64: "abc", mime_type: "audio/webm" }),
    );
  });

  it("createLivingPlan POSTs empty body to /living-plan", async () => {
    const plan = {
      id: "plan-1",
      goals: ["Speak"],
      focus: "Conversation",
      upcoming_topics: ["Greetings"],
      difficulty: "intermediate",
      selected_path_id: "conv",
      proposed_paths: [
        {
          id: "conv",
          title: "Conversation",
          summary: "Talk first",
          recommended: true,
        },
      ],
      revisable: true,
      target_language: "en",
      l1: "ru",
      lessons: [
        {
          id: "lesson-1",
          scheduled_at: "2026-03-02T07:00:00Z",
          timezone: "Europe/Moscow",
        },
      ],
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, plan));
    vi.stubGlobal("fetch", fetchMock);
    await expect(createLivingPlan(RUNNING)).resolves.toEqual(plan);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://127.0.0.1:8765/living-plan");
    expect(init.method).toBe("POST");
    expect(init.body).toBe("{}");
  });

  it("fetchLivingPlan GETs /living-plan", async () => {
    const plan = { id: "plan-1", lessons: [] };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, plan));
    vi.stubGlobal("fetch", fetchMock);
    await expect(fetchLivingPlan(RUNNING)).resolves.toEqual(plan);
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8765/living-plan",
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer tok-123" }),
      }),
    );
  });

  it("createLivingPlan surfaces schedule_unusable as shaped error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(422, {
          code: "schedule_unusable",
          message: "no usable lesson times",
          retryable: false,
        }),
      ),
    );
    await expect(createLivingPlan(RUNNING)).rejects.toMatchObject({
      code: "schedule_unusable",
      status: 422,
    });
  });

  it("fetchLivingPlan surfaces living_plan_not_found as shaped 404", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(404, {
          code: "living_plan_not_found",
          message: "living plan has not been created yet",
          retryable: false,
        }),
      ),
    );
    await expect(fetchLivingPlan(RUNNING)).rejects.toMatchObject({
      code: "living_plan_not_found",
      status: 404,
      retryable: false,
    });
  });

  it("fetchLivingPlan surfaces plan_inconsistent as shaped 500", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(500, {
          code: "plan_inconsistent",
          message: "plan_complete is set but no living plan row exists",
          retryable: false,
        }),
      ),
    );
    await expect(fetchLivingPlan(RUNNING)).rejects.toMatchObject({
      code: "plan_inconsistent",
      status: 500,
      retryable: false,
    });
  });
});

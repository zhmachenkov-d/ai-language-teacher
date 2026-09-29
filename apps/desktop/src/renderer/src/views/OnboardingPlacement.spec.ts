import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { nextTick } from "vue";
import {
  createRouter,
  createWebHashHistory,
  RouterView,
  type Router,
} from "vue-router";
import OnboardingPlacement from "./OnboardingPlacement.vue";
import OnboardingPlanStub from "./OnboardingPlanStub.vue";
import type {
  LearnerProfile,
  PlacementItemsPublic,
} from "../services/teacherClient";

const RUNNING_AUTH = {
  state: "running" as const,
  base_url: "http://127.0.0.1:8765",
  bearer: "tok-123",
};

const BASE_LEARNER: LearnerProfile = {
  id: "learner-1",
  target_language: "en",
  l1: "ru",
  timezone: "Europe/Moscow",
  address_as: "Саша",
  age: 30,
  goals: ["Учёба"],
  desired_outcome: ["Уверенный разговор"],
  interests: ["Технологии"],
  emphasis: ["Говорение"],
  lesson_duration_minutes: 45,
  weekly_slots: [{ weekday: 0, start_minute: 540 }],
  intake_step: "complete",
  consent_mic: true,
  consent_telegram: false,
  consent_ai: true,
  consent_privacy: true,
  consent_complete: true,
  placement_stage: "briefing",
  placement_items: null,
  placement_written_answers: [],
  placement_written_score: null,
  placement_listening_generated: false,
  placement_listening_played: false,
  placement_listening_answers: [],
  placement_listening_score: null,
  placement_speaking_transcript: null,
  placement_speaking_score: null,
  placement_complete: false,
  plan_complete: false,
};

const PUBLIC_ITEMS: PlacementItemsPublic = {
  written: Array.from({ length: 5 }, (_, i) => ({
    prompt: `Written Q${i}`,
    options: ["a", "b", "c"],
  })),
  listening: {
    questions: Array.from({ length: 3 }, (_, i) => ({
      prompt: `Listening Q${i}`,
      options: ["a", "b", "c"],
    })),
  },
  speaking_prompts: ["Tell me about your day.", "Describe your job.", "Plans?"],
};

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function mockTeacherBridge(): void {
  Object.defineProperty(window, "teacher", {
    configurable: true,
    value: {
      getAuth: vi.fn().mockResolvedValue(RUNNING_AUTH),
      retry: vi.fn().mockResolvedValue(RUNNING_AUTH),
      onStatusChange: vi.fn().mockReturnValue(() => undefined),
    },
  });
}

/** Minimal MediaRecorder double: `stop()` synchronously fires one chunk + `onstop`,
 * mirroring the real API closely enough to drive `onRecordingStopped`. */
class FakeMediaRecorder {
  ondataavailable: ((event: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;
  mimeType = "audio/webm";
  constructor(public stream: MediaStream) {}
  start(): void {
    /* no-op */
  }
  stop(): void {
    this.ondataavailable?.({
      data: new Blob(["fake-audio-bytes"], { type: this.mimeType }),
    });
    this.onstop?.();
  }
}

function fakeMediaStream(): {
  stream: MediaStream;
  stopTrack: ReturnType<typeof vi.fn>;
} {
  const stopTrack = vi.fn();
  const stream = {
    getTracks: () => [{ stop: stopTrack }],
  } as unknown as MediaStream;
  return { stream, stopTrack };
}

/** Stubs `navigator.mediaDevices.getUserMedia` + `window.MediaRecorder` so
 * `micAvailable()` reports true and the speaking record flow can run. */
function mockMicSupport(getUserMediaImpl?: () => Promise<MediaStream>): {
  getUserMedia: ReturnType<typeof vi.fn>;
} {
  const { stream } = fakeMediaStream();
  const getUserMedia = vi
    .fn()
    .mockImplementation(getUserMediaImpl ?? (() => Promise.resolve(stream)));
  Object.defineProperty(navigator, "mediaDevices", {
    configurable: true,
    value: { getUserMedia },
  });
  vi.stubGlobal(
    "MediaRecorder",
    FakeMediaRecorder as unknown as typeof MediaRecorder,
  );
  return { getUserMedia };
}

type RouteHandler = (init: RequestInit | undefined) => Response;

/** Dispatches by "METHOD /path" so each test only defines the endpoints it exercises. */
function dispatcher(
  handlers: Record<string, RouteHandler>,
): ReturnType<typeof vi.fn> {
  return vi.fn((url: string, init?: RequestInit) => {
    const path = url.replace("http://127.0.0.1:8765", "");
    const key = `${init?.method ?? "GET"} ${path}`;
    const handler = handlers[key];
    if (!handler) {
      return Promise.resolve(
        jsonResponse(500, {
          code: "unhandled",
          message: `no handler for ${key}`,
          retryable: false,
        }),
      );
    }
    return Promise.resolve(handler(init));
  });
}

async function mountPlacement(fetchImpl: ReturnType<typeof vi.fn>): Promise<{
  wrapper: ReturnType<typeof mount>;
  router: Router;
}> {
  vi.stubGlobal("fetch", fetchImpl);
  window.location.hash = "#/onboarding/placement";
  const router = createRouter({
    history: createWebHashHistory(),
    routes: [
      { path: "/", redirect: "/onboarding/placement" },
      {
        path: "/onboarding/placement",
        name: "onboarding-placement",
        component: OnboardingPlacement,
      },
      {
        path: "/onboarding/plan",
        name: "onboarding-plan",
        component: OnboardingPlanStub,
      },
      {
        path: "/settings",
        name: "settings",
        component: { template: "<div />" },
      },
    ],
  });
  const wrapper = mount(RouterView, { global: { plugins: [router] } });
  await router.isReady();
  if (router.currentRoute.value.name !== "onboarding-placement") {
    await router.replace({ name: "onboarding-placement" });
  }
  await flushPromises();
  await nextTick();
  return { wrapper, router };
}

describe("OnboardingPlacement", () => {
  beforeEach(() => {
    mockTeacherBridge();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    delete (navigator as unknown as { mediaDevices?: unknown }).mediaDevices;
  });

  it("Config missing on briefing → Далее blocks with Settings path + retry, no fake advance", async () => {
    const fetchMock = dispatcher({
      "GET /learner": () => jsonResponse(200, BASE_LEARNER),
      "POST /placement/items": () =>
        jsonResponse(422, {
          code: "llm_config_missing",
          message: "LLM API key is not configured",
          retryable: true,
        }),
    });
    const { wrapper } = await mountPlacement(fetchMock);
    expect(wrapper.find('[data-testid="placement-briefing"]').exists()).toBe(
      true,
    );

    await wrapper.get('[data-testid="briefing-next"]').trigger("click");
    await flushPromises();

    expect(wrapper.get('[data-testid="generate-error"]').text()).toContain(
      "Настройте ключ ИИ",
    );
    expect(wrapper.find(".settings-link").exists()).toBe(true);
    // Still on briefing — no PATCH advancing the stage happened.
    expect(wrapper.find('[data-testid="placement-briefing"]').exists()).toBe(
      true,
    );
    expect(wrapper.find('[data-testid="placement-written"]').exists()).toBe(
      false,
    );
    const patchCalls = fetchMock.mock.calls.filter(
      (c) => (c[1] as RequestInit | undefined)?.method === "PATCH",
    );
    expect(patchCalls).toHaveLength(0);
    wrapper.unmount();
  });

  it("briefing Далее generates items and advances to written with a timer", async () => {
    const fetchMock = dispatcher({
      "GET /learner": () => jsonResponse(200, BASE_LEARNER),
      "POST /placement/items": () => jsonResponse(200, PUBLIC_ITEMS),
      "PATCH /learner": () =>
        jsonResponse(200, { ...BASE_LEARNER, placement_stage: "written" }),
    });
    const { wrapper } = await mountPlacement(fetchMock);
    await wrapper.get('[data-testid="briefing-next"]').trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="placement-written"]').exists()).toBe(
      true,
    );
    expect(wrapper.findAll(".item")).toHaveLength(5);
    expect(wrapper.get('[data-testid="written-timer"]').text()).toContain(
      "05:00",
    );
    wrapper.unmount();
  });

  it("written stage timer end auto-submits answers and advances to listening", async () => {
    vi.useFakeTimers();
    const patchBodies: unknown[] = [];
    const fetchMock = dispatcher({
      "GET /learner": () =>
        jsonResponse(200, {
          ...BASE_LEARNER,
          placement_stage: "written",
          placement_items: PUBLIC_ITEMS,
        }),
      "PATCH /learner": (_init) => {
        const body = JSON.parse(String(_init?.body ?? "{}"));
        patchBodies.push(body);
        return jsonResponse(200, {
          ...BASE_LEARNER,
          placement_stage: "listening",
          placement_items: PUBLIC_ITEMS,
          placement_written_answers: body.placement_written_answers ?? [],
          placement_written_score: 0,
        });
      },
      "POST /placement/listening/audio": () =>
        jsonResponse(200, { audio_base64: "aGVsbG8=", mime_type: "audio/wav" }),
    });
    const { wrapper } = await mountPlacement(fetchMock);
    expect(wrapper.find('[data-testid="placement-written"]').exists()).toBe(
      true,
    );

    await vi.advanceTimersByTimeAsync(300_000);
    await flushPromises();

    expect(patchBodies).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          placement_written_answers: [-1, -1, -1, -1, -1],
          placement_stage: "listening",
        }),
      ]),
    );
    expect(wrapper.find('[data-testid="placement-listening"]').exists()).toBe(
      true,
    );
    wrapper.unmount();
    vi.useRealTimers();
  });

  it("resumes mid-placement at listening: fetches audio and shows comprehension questions", async () => {
    const fetchMock = dispatcher({
      "GET /learner": () =>
        jsonResponse(200, {
          ...BASE_LEARNER,
          placement_stage: "listening",
          placement_items: PUBLIC_ITEMS,
          placement_written_score: 1,
        }),
      "POST /placement/listening/audio": () =>
        jsonResponse(200, { audio_base64: "aGVsbG8=", mime_type: "audio/wav" }),
    });
    const { wrapper } = await mountPlacement(fetchMock);
    expect(wrapper.find('[data-testid="placement-listening"]').exists()).toBe(
      true,
    );
    expect(wrapper.find('[data-testid="listening-play"]').exists()).toBe(true);
    expect(wrapper.findAll(".item")).toHaveLength(3);
    wrapper.unmount();
  });

  it("blocks listening submit before @ended (Russian copy, no PATCH), allows it after", async () => {
    const fetchMock = dispatcher({
      "GET /learner": () =>
        jsonResponse(200, {
          ...BASE_LEARNER,
          placement_stage: "listening",
          placement_items: PUBLIC_ITEMS,
          placement_written_score: 1,
        }),
      "POST /placement/listening/audio": () =>
        jsonResponse(200, { audio_base64: "aGVsbG8=", mime_type: "audio/wav" }),
      "PATCH /learner": () =>
        jsonResponse(200, {
          ...BASE_LEARNER,
          placement_stage: "speaking",
          placement_items: PUBLIC_ITEMS,
          placement_written_score: 1,
          placement_listening_generated: true,
          placement_listening_played: true,
          placement_listening_score: 1,
        }),
    });
    const { wrapper } = await mountPlacement(fetchMock);
    expect(wrapper.find('[data-testid="listening-audio"]').exists()).toBe(true);

    await wrapper.get('[data-testid="listening-submit"]').trigger("click");
    await flushPromises();
    expect(
      wrapper.get('[data-testid="listening-save-error"]').text(),
    ).toContain("прослушайте");
    expect(
      fetchMock.mock.calls.filter(
        (c) => (c[1] as RequestInit | undefined)?.method === "PATCH",
      ),
    ).toHaveLength(0);
    // Still on listening — the must-play gate blocked the transition.
    expect(wrapper.find('[data-testid="placement-listening"]').exists()).toBe(
      true,
    );

    await wrapper.get('[data-testid="listening-audio"]').trigger("ended");
    await wrapper.get('[data-testid="listening-submit"]').trigger("click");
    await flushPromises();

    expect(
      fetchMock.mock.calls.filter(
        (c) => (c[1] as RequestInit | undefined)?.method === "PATCH",
      ),
    ).toHaveLength(1);
    expect(wrapper.find('[data-testid="placement-speaking"]').exists()).toBe(
      true,
    );
    wrapper.unmount();
  });

  it("TTS failure on listening shows retryable error, no fake pass", async () => {
    const fetchMock = dispatcher({
      "GET /learner": () =>
        jsonResponse(200, {
          ...BASE_LEARNER,
          placement_stage: "listening",
          placement_items: PUBLIC_ITEMS,
          placement_written_score: 1,
        }),
      "POST /placement/listening/audio": () =>
        jsonResponse(422, {
          code: "voice_unavailable",
          message: "local TTS engine not found",
          retryable: true,
        }),
    });
    const { wrapper } = await mountPlacement(fetchMock);
    expect(wrapper.get('[data-testid="listening-audio-error"]').exists()).toBe(
      true,
    );
    expect(wrapper.find('[data-testid="listening-audio"]').exists()).toBe(
      false,
    );
    expect(wrapper.find('[data-testid="listening-play"]').exists()).toBe(false);
    wrapper.unmount();
  });

  it("mic unavailable on speaking shows a Russian error and never calls transcribe", async () => {
    const fetchMock = dispatcher({
      "GET /learner": () =>
        jsonResponse(200, {
          ...BASE_LEARNER,
          placement_stage: "speaking",
          placement_items: PUBLIC_ITEMS,
          placement_written_score: 1,
          placement_listening_generated: true,
          placement_listening_played: true,
          placement_listening_score: 1,
        }),
    });
    const { wrapper } = await mountPlacement(fetchMock);
    expect(wrapper.find('[data-testid="placement-speaking"]').exists()).toBe(
      true,
    );

    await wrapper.get('[data-testid="speaking-record"]').trigger("click");
    await flushPromises();

    expect(wrapper.get('[data-testid="mic-error"]').text()).toContain(
      "Микрофон",
    );
    const transcribeCalls = fetchMock.mock.calls.filter(([url]) =>
      String(url).includes("/placement/speaking/transcribe"),
    );
    expect(transcribeCalls).toHaveLength(0);
    // Text-only completion stays blocked: no transcript yet → Готово disabled.
    expect(
      (
        wrapper.get('[data-testid="speaking-finish"]')
          .element as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    wrapper.unmount();
  });

  it("record → stop calls transcribe and shows the recognized transcript", async () => {
    mockMicSupport();
    const fetchMock = dispatcher({
      "GET /learner": () =>
        jsonResponse(200, {
          ...BASE_LEARNER,
          placement_stage: "speaking",
          placement_items: PUBLIC_ITEMS,
          placement_written_score: 1,
          placement_listening_generated: true,
          placement_listening_played: true,
          placement_listening_score: 1,
        }),
      "POST /placement/speaking/transcribe": () =>
        jsonResponse(200, {
          ...BASE_LEARNER,
          placement_stage: "speaking",
          placement_items: PUBLIC_ITEMS,
          placement_written_score: 1,
          placement_listening_generated: true,
          placement_listening_played: true,
          placement_listening_score: 1,
          placement_speaking_transcript: "hello this is my answer",
          placement_speaking_score: 0.5,
        }),
    });
    const { wrapper } = await mountPlacement(fetchMock);

    await wrapper.get('[data-testid="speaking-record"]').trigger("click");
    await flushPromises();
    expect(wrapper.get('[data-testid="speaking-record"]').text()).toContain(
      "Остановить запись",
    );

    await wrapper.get('[data-testid="speaking-record"]').trigger("click");
    // FileReader.readAsDataURL completes on a macrotask in happy-dom, so a
    // single microtask flush isn't enough — wait for the transcribe POST.
    await vi.waitUntil(() =>
      fetchMock.mock.calls.some(([url]) =>
        String(url).includes("/placement/speaking/transcribe"),
      ),
    );
    await flushPromises();

    const transcribeCalls = fetchMock.mock.calls.filter(([url]) =>
      String(url).includes("/placement/speaking/transcribe"),
    );
    expect(transcribeCalls).toHaveLength(1);
    expect(wrapper.get('[data-testid="speaking-transcript"]').text()).toContain(
      "hello this is my answer",
    );
    expect(
      (
        wrapper.get('[data-testid="speaking-finish"]')
          .element as HTMLButtonElement
      ).disabled,
    ).toBe(false);
    wrapper.unmount();
  });

  it("voice_unavailable on transcribe shows speaking-save-error and keeps finish disabled", async () => {
    mockMicSupport();
    const fetchMock = dispatcher({
      "GET /learner": () =>
        jsonResponse(200, {
          ...BASE_LEARNER,
          placement_stage: "speaking",
          placement_items: PUBLIC_ITEMS,
          placement_written_score: 1,
          placement_listening_generated: true,
          placement_listening_played: true,
          placement_listening_score: 1,
        }),
      "POST /placement/speaking/transcribe": () =>
        jsonResponse(422, {
          code: "voice_unavailable",
          message: "local STT engine not found",
          retryable: true,
        }),
    });
    const { wrapper } = await mountPlacement(fetchMock);

    await wrapper.get('[data-testid="speaking-record"]').trigger("click");
    await flushPromises();
    await wrapper.get('[data-testid="speaking-record"]').trigger("click");
    // FileReader.readAsDataURL completes on a macrotask in happy-dom, so a
    // single microtask flush isn't enough — wait for the transcribe attempt.
    await vi.waitUntil(() =>
      fetchMock.mock.calls.some(([url]) =>
        String(url).includes("/placement/speaking/transcribe"),
      ),
    );
    await flushPromises();

    expect(wrapper.get('[data-testid="speaking-save-error"]').text()).toContain(
      "local STT engine not found",
    );
    expect(wrapper.find(".settings-link").exists()).toBe(true);
    expect(
      (
        wrapper.get('[data-testid="speaking-finish"]')
          .element as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    wrapper.unmount();
  });

  it("text-only complete rejected by the server surfaces an error and stays on placement", async () => {
    const fetchMock = dispatcher({
      "GET /learner": () =>
        jsonResponse(200, {
          ...BASE_LEARNER,
          placement_stage: "speaking",
          placement_items: PUBLIC_ITEMS,
          placement_written_score: 1,
          placement_listening_generated: true,
          placement_listening_played: true,
          placement_listening_score: 1,
          placement_speaking_transcript: "a real transcript",
          placement_speaking_score: 0.6,
        }),
      "PATCH /learner": () =>
        jsonResponse(422, {
          code: "placement_listening_incomplete",
          message: "listening result is required before placement_complete",
          retryable: false,
        }),
    });
    const { wrapper, router } = await mountPlacement(fetchMock);
    await wrapper.get('[data-testid="speaking-finish"]').trigger("click");
    await flushPromises();

    expect(wrapper.get('[data-testid="complete-error"]').text()).toContain(
      "listening result is required",
    );
    expect(router.currentRoute.value.name).toBe("onboarding-placement");
    wrapper.unmount();
  });

  it("full finish hands off to the plan stub (HANDOFF: PLAN_STUB)", async () => {
    const fetchMock = dispatcher({
      "GET /learner": () =>
        jsonResponse(200, {
          ...BASE_LEARNER,
          placement_stage: "speaking",
          placement_items: PUBLIC_ITEMS,
          placement_written_score: 1,
          placement_listening_generated: true,
          placement_listening_played: true,
          placement_listening_score: 1,
          placement_speaking_transcript: "a real transcript",
          placement_speaking_score: 0.6,
        }),
      "PATCH /learner": () =>
        jsonResponse(200, {
          ...BASE_LEARNER,
          placement_stage: "complete",
          placement_complete: true,
          placement_speaking_transcript: "a real transcript",
        }),
    });
    const { wrapper, router } = await mountPlacement(fetchMock);
    await wrapper.get('[data-testid="speaking-finish"]').trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.name).toBe("onboarding-plan");
    expect(wrapper.find('[data-testid="onboarding-plan-stub"]').exists()).toBe(
      true,
    );
    wrapper.unmount();
  });

  it("already placement_complete on load redirects to the plan stub", async () => {
    const fetchMock = dispatcher({
      "GET /learner": () =>
        jsonResponse(200, {
          ...BASE_LEARNER,
          placement_stage: "complete",
          placement_complete: true,
        }),
    });
    const { wrapper, router } = await mountPlacement(fetchMock);
    expect(router.currentRoute.value.name).toBe("onboarding-plan");
    expect(wrapper.find('[data-testid="onboarding-plan-stub"]').exists()).toBe(
      true,
    );
    wrapper.unmount();
  });
});

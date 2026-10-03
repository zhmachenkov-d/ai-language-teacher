import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { nextTick } from "vue";
import { createRouter, createWebHashHistory, type Router } from "vue-router";
import { RouterView } from "vue-router";
import * as gate from "../onboarding/gate";
import type { LearnerProfile, LivingPlanProjection } from "../services/teacherClient";
import PlanView from "./PlanView.vue";

const RUNNING_AUTH = {
  state: "running" as const,
  base_url: "http://127.0.0.1:8765",
  bearer: "test-bearer-token",
};

const SAMPLE_PLAN: LivingPlanProjection = {
  id: "plan-1",
  goals: ["Разговорный английский", "Travel vocabulary"],
  focus: "Everyday speaking",
  upcoming_topics: ["Airport check-in", "Hotel booking"],
  difficulty: "A2",
  selected_path_id: "path-a",
  proposed_paths: [],
  revisable: true,
  target_language: "en",
  l1: "ru",
  lessons: [],
};

const BASE_LEARNER: LearnerProfile = {
  id: "learner-1",
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
  intake_step: "complete",
  consent_mic: true,
  consent_telegram: true,
  consent_ai: true,
  consent_privacy: true,
  consent_complete: true,
  placement_stage: "complete",
  placement_items: null,
  placement_written_answers: [],
  placement_written_score: null,
  placement_listening_generated: false,
  placement_listening_played: false,
  placement_listening_answers: [],
  placement_listening_score: null,
  placement_speaking_transcript: null,
  placement_speaking_score: null,
  placement_complete: true,
  plan_complete: false,
};

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function mockTeacherBridge(
  overrides: Partial<typeof RUNNING_AUTH & { message?: string }> = {},
): {
  getAuth: ReturnType<typeof vi.fn>;
  retry: ReturnType<typeof vi.fn>;
  onStatusChange: ReturnType<typeof vi.fn>;
} {
  const status = { ...RUNNING_AUTH, ...overrides };
  const getAuth = vi.fn().mockResolvedValue(status);
  const retry = vi.fn().mockResolvedValue(status);
  const onStatusChange = vi.fn().mockReturnValue(() => undefined);
  Object.defineProperty(window, "teacher", {
    configurable: true,
    value: { getAuth, retry, onStatusChange },
  });
  return { getAuth, retry, onStatusChange };
}

async function mountPlan(): Promise<{
  wrapper: ReturnType<typeof mount>;
  router: Router;
}> {
  // Hash must be set before createWebHashHistory reads the location.
  window.location.hash = "#/plan";
  const router = createRouter({
    history: createWebHashHistory(),
    routes: [
      { path: "/", redirect: "/plan" },
      { path: "/plan", name: "plan", component: PlanView },
      {
        path: "/calendar",
        name: "calendar",
        component: { template: "<div data-testid='calendar-stub'>calendar</div>" },
      },
      {
        path: "/onboarding/plan",
        name: "onboarding-plan",
        component: {
          template: "<div data-testid='onboarding-plan-stub'>onboarding-plan</div>",
        },
      },
      {
        path: "/onboarding",
        name: "onboarding",
        component: { template: "<div>onboarding</div>" },
      },
      {
        path: "/onboarding/consent",
        name: "onboarding-consent",
        component: { template: "<div>consent</div>" },
      },
      {
        path: "/onboarding/placement",
        name: "onboarding-placement",
        component: { template: "<div>placement</div>" },
      },
    ],
  });
  const wrapper = mount(RouterView, {
    global: { plugins: [router] },
  });
  await router.isReady();
  await flushPromises();
  await nextTick();
  return { wrapper, router };
}

describe("PlanView — Living plan document", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("happy path: three surface sections with API goals/focus/topics", async () => {
    mockTeacherBridge();
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, SAMPLE_PLAN));
    vi.stubGlobal("fetch", fetchMock);
    const { wrapper } = await mountPlan();

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8765/living-plan",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer test-bearer-token",
        }),
      }),
    );
    expect(wrapper.find('[data-testid="plan-view"]').exists()).toBe(true);
    expect(wrapper.get("h1").text()).toBe("План");
    expect(wrapper.text()).toContain("ЦЕЛИ");
    expect(wrapper.text()).toContain("ФОКУС");
    expect(wrapper.text()).toContain("БЛИЖАЙШИЕ ТЕМЫ");
    expect(wrapper.text()).toContain("Разговорный английский");
    expect(wrapper.text()).toContain("Everyday speaking");
    expect(wrapper.text()).toContain("Airport check-in");
    expect(wrapper.find('[data-testid="plan-empty"]').exists()).toBe(false);
    expect(wrapper.find("input").exists()).toBe(false);
    expect(wrapper.find("textarea").exists()).toBe(false);
    wrapper.unmount();
  });

  it("soft-empty 200: three sections with «Пока пусто» for empty fields", async () => {
    mockTeacherBridge();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(200, {
          ...SAMPLE_PLAN,
          goals: [],
          focus: "   ",
          upcoming_topics: [],
        }),
      ),
    );
    const { wrapper } = await mountPlan();

    expect(wrapper.find('[data-testid="plan-section-goals"]').exists()).toBe(
      true,
    );
    expect(wrapper.find('[data-testid="plan-section-focus"]').exists()).toBe(
      true,
    );
    expect(wrapper.find('[data-testid="plan-section-topics"]').exists()).toBe(
      true,
    );
    expect(wrapper.find('[data-testid="goals-soft-empty"]').text()).toBe(
      "Пока пусто",
    );
    const focus = wrapper.get('[data-testid="plan-focus"]');
    expect(focus.text()).toBe("Пока пусто");
    expect(focus.classes()).toContain("soft-empty");
    expect(wrapper.find('[data-testid="topics-soft-empty"]').text()).toBe(
      "Пока пусто",
    );
    expect(wrapper.find('[data-testid="plan-empty"]').exists()).toBe(false);
    wrapper.unmount();
  });

  it("coerce bad arrays to [] before render (soft-empty, not Option B)", async () => {
    mockTeacherBridge();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(200, {
          ...SAMPLE_PLAN,
          goals: "not-an-array",
          focus: "ok focus",
          upcoming_topics: null,
        }),
      ),
    );
    const { wrapper } = await mountPlan();

    expect(wrapper.find('[data-testid="goals-soft-empty"]').text()).toBe(
      "Пока пусто",
    );
    expect(wrapper.get('[data-testid="plan-focus"]').text()).toBe("ok focus");
    expect(wrapper.find('[data-testid="topics-soft-empty"]').text()).toBe(
      "Пока пусто",
    );
    expect(wrapper.find('[data-testid="plan-empty"]').exists()).toBe(false);
    wrapper.unmount();
  });

  it("loading: shows «Загрузка…» and no sections while auth/plan fetch in flight", async () => {
    let releaseAuth!: (value: unknown) => void;
    const hungAuth = new Promise((resolve) => {
      releaseAuth = resolve;
    });
    Object.defineProperty(window, "teacher", {
      configurable: true,
      value: {
        getAuth: vi.fn().mockReturnValue(hungAuth),
        retry: vi.fn(),
        onStatusChange: vi.fn().mockReturnValue(() => undefined),
      },
    });
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    window.location.hash = "#/plan";
    const router = createRouter({
      history: createWebHashHistory(),
      routes: [{ path: "/plan", name: "plan", component: PlanView }],
    });
    const wrapper = mount(RouterView, { global: { plugins: [router] } });
    await router.isReady();
    await nextTick();

    expect(wrapper.find('[data-testid="plan-loading"]').text()).toContain(
      "Загрузка…",
    );
    expect(wrapper.find('[data-testid="plan-section-goals"]').exists()).toBe(
      false,
    );
    expect(fetchMock).not.toHaveBeenCalled();

    releaseAuth(RUNNING_AUTH);
    await flushPromises();
    wrapper.unmount();
  });

  it("teacher not running: status + retry; no GET until running", async () => {
    const getAuth = vi.fn().mockResolvedValue({
      state: "error",
      base_url: "",
      bearer: null,
      message: "Учитель не запущен",
    });
    const retry = vi.fn().mockResolvedValue({ ...RUNNING_AUTH });
    Object.defineProperty(window, "teacher", {
      configurable: true,
      value: {
        getAuth,
        retry,
        onStatusChange: vi.fn().mockReturnValue(() => undefined),
      },
    });
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, SAMPLE_PLAN));
    vi.stubGlobal("fetch", fetchMock);
    const { wrapper } = await mountPlan();

    const banner = wrapper.find('[data-testid="launch-failure-banner"]');
    expect(banner.exists()).toBe(true);
    expect(banner.text()).toContain("Учитель не запущен");
    expect(fetchMock).not.toHaveBeenCalled();

    await banner.get("button").trigger("click");
    await flushPromises();

    expect(retry).toHaveBeenCalledTimes(1);
    expect(wrapper.find('[data-testid="launch-failure-banner"]').exists()).toBe(
      false,
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8765/living-plan",
      expect.anything(),
    );
    expect(wrapper.text()).toContain("Everyday speaking");
    wrapper.unmount();
  });

  it("auth becomes running via onStatusChange: auto-fetches plan", async () => {
    let statusCallback:
      | ((status: typeof RUNNING_AUTH) => void)
      | undefined;
    const getAuth = vi.fn().mockResolvedValue({
      state: "starting",
      base_url: "",
      bearer: null,
    });
    const onStatusChange = vi
      .fn()
      .mockImplementation((cb: (status: typeof RUNNING_AUTH) => void) => {
        statusCallback = cb;
        return () => undefined;
      });
    Object.defineProperty(window, "teacher", {
      configurable: true,
      value: { getAuth, retry: vi.fn(), onStatusChange },
    });
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, SAMPLE_PLAN));
    vi.stubGlobal("fetch", fetchMock);
    const { wrapper } = await mountPlan();

    expect(fetchMock).not.toHaveBeenCalled();
    expect(statusCallback).toBeDefined();

    statusCallback?.({ ...RUNNING_AUTH });
    await flushPromises();

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8765/living-plan",
      expect.anything(),
    );
    expect(wrapper.text()).toContain("Разговорный английский");
    wrapper.unmount();
  });

  it("non-404 API error: inline message + retry reloads plan", async () => {
    mockTeacherBridge();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse(500, {
          code: "plan_inconsistent",
          message: "План повреждён",
          retryable: true,
        }),
      )
      .mockResolvedValueOnce(jsonResponse(200, SAMPLE_PLAN));
    vi.stubGlobal("fetch", fetchMock);
    const { wrapper } = await mountPlan();

    expect(wrapper.find('[data-testid="plan-error"]').text()).toContain(
      "План повреждён",
    );
    expect(wrapper.find('[data-testid="plan-empty"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="plan-section-goals"]').exists()).toBe(
      false,
    );

    await wrapper.get('[data-testid="plan-retry"]').trigger("click");
    await flushPromises();

    expect(wrapper.text()).toContain("Everyday speaking");
    expect(wrapper.find('[data-testid="plan-error"]').exists()).toBe(false);
    wrapper.unmount();
  });

  it("API error without message uses fallback copy", async () => {
    mockTeacherBridge();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(500, {
          code: "server_error",
          message: "",
          retryable: true,
        }),
      ),
    );
    const { wrapper } = await mountPlan();

    // TeacherApiError still constructed with empty message → fallback in view
    expect(wrapper.find('[data-testid="plan-error"]').text()).toContain(
      "Не удалось загрузить план",
    );
    wrapper.unmount();
  });

  it("404 living_plan_not_found + mid-GATE: Option B empty + «Продолжить настройку»", async () => {
    mockTeacherBridge();
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (String(url).endsWith("/living-plan")) {
        return Promise.resolve(
          jsonResponse(404, {
            code: "living_plan_not_found",
            message: "Living plan not found",
            retryable: false,
          }),
        );
      }
      if (String(url).endsWith("/learner")) {
        return Promise.resolve(jsonResponse(200, BASE_LEARNER));
      }
      return Promise.resolve(jsonResponse(404, { code: "not_found" }));
    });
    vi.stubGlobal("fetch", fetchMock);
    const { wrapper, router } = await mountPlan();

    expect(wrapper.find('[data-testid="plan-empty"]').text()).toContain(
      "План обучения ещё не готов.",
    );
    expect(wrapper.find('[data-testid="plan-section-goals"]').exists()).toBe(
      false,
    );
    const cta = wrapper.get('[data-testid="plan-empty-cta"]');
    expect(cta.text()).toBe("Продолжить настройку");

    await cta.trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.name).toBe("onboarding-plan");
    wrapper.unmount();
  });

  it("404 + fetchLearner failure: empty body, omit CTA", async () => {
    mockTeacherBridge();
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (String(url).endsWith("/living-plan")) {
        return Promise.resolve(
          jsonResponse(404, {
            code: "living_plan_not_found",
            message: "Living plan not found",
            retryable: false,
          }),
        );
      }
      if (String(url).endsWith("/learner")) {
        return Promise.resolve(
          jsonResponse(500, {
            code: "server_error",
            message: "Сбой сервера",
            retryable: true,
          }),
        );
      }
      return Promise.resolve(jsonResponse(404, { code: "not_found" }));
    });
    vi.stubGlobal("fetch", fetchMock);
    const { wrapper } = await mountPlan();

    expect(wrapper.find('[data-testid="plan-empty"]').text()).toContain(
      "План обучения ещё не готов.",
    );
    expect(wrapper.find('[data-testid="plan-empty-cta"]').exists()).toBe(false);
    wrapper.unmount();
  });

  it("401: rehydrates auth without tight plan-retry loop", async () => {
    const { getAuth } = mockTeacherBridge();
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(401, {
        code: "unauthorized",
        message: "Нет доступа",
        retryable: false,
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { wrapper } = await mountPlan();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(getAuth).toHaveBeenCalledTimes(2); // initial + rehydrate
    expect(wrapper.find('[data-testid="plan-error"]').text()).toContain(
      "Нет доступа",
    );
    wrapper.unmount();
  });

  it("404 + gateDestination calendar: «К календарю» navigates to calendar", async () => {
    mockTeacherBridge();
    vi.spyOn(gate, "gateDestination").mockReturnValue("calendar");
    vi.spyOn(gate, "isOnboardingRoute").mockReturnValue(false);
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (String(url).endsWith("/living-plan")) {
        return Promise.resolve(
          jsonResponse(404, {
            code: "living_plan_not_found",
            message: "Living plan not found",
            retryable: false,
          }),
        );
      }
      if (String(url).endsWith("/learner")) {
        return Promise.resolve(jsonResponse(200, BASE_LEARNER));
      }
      return Promise.resolve(jsonResponse(404, { code: "not_found" }));
    });
    vi.stubGlobal("fetch", fetchMock);
    const { wrapper, router } = await mountPlan();

    expect(wrapper.find('[data-testid="plan-view"]').exists()).toBe(true);
    const cta = wrapper.get('[data-testid="plan-empty-cta"]');
    expect(cta.text()).toBe("К календарю");
    await cta.trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.name).toBe("calendar");
    wrapper.unmount();
  });
});

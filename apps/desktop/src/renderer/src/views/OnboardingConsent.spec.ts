import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { nextTick } from "vue";
import { createRouter, createWebHashHistory, type Router } from "vue-router";
import { RouterView } from "vue-router";
import OnboardingConsent from "./OnboardingConsent.vue";
import OnboardingPlacement from "./OnboardingPlacement.vue";
import type { LearnerProfile } from "../services/teacherClient";

const RUNNING_AUTH = {
  state: "running" as const,
  base_url: "http://127.0.0.1:8765",
  bearer: "tok-123",
};

const INTAKE_DONE: LearnerProfile = {
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
  consent_mic: false,
  consent_telegram: false,
  consent_ai: false,
  consent_privacy: false,
  consent_complete: false,
};

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function mockBridges(quit = vi.fn().mockResolvedValue(undefined)): void {
  Object.defineProperty(window, "teacher", {
    configurable: true,
    value: {
      getAuth: vi.fn().mockResolvedValue(RUNNING_AUTH),
      retry: vi.fn().mockResolvedValue(RUNNING_AUTH),
      onStatusChange: vi.fn().mockReturnValue(() => undefined),
    },
  });
  Object.defineProperty(window, "desktop", {
    configurable: true,
    value: { scaffold: "1.1", quit },
  });
}

async function mountConsent(fetchImpl: ReturnType<typeof vi.fn>): Promise<{
  wrapper: ReturnType<typeof mount>;
  router: Router;
  quit: ReturnType<typeof vi.fn>;
}> {
  const quit = vi.fn().mockResolvedValue(undefined);
  mockBridges(quit);
  vi.stubGlobal("fetch", fetchImpl);
  // Set the hash *before* creating the router: `createWebHashHistory()` reads
  // the current hash at construction time. If a prior test's hash (e.g.
  // `#/onboarding/placement`) is still set, creating the router first would
  // resolve its initial navigation against that stale route, mounting the
  // wrong (now-real, fetching) view and double-consuming this test's single
  // mocked Response body before the intended navigation even runs.
  window.location.hash = "#/onboarding/consent";
  const router = createRouter({
    history: createWebHashHistory(),
    routes: [
      { path: "/", redirect: "/onboarding/consent" },
      {
        path: "/onboarding/consent",
        name: "onboarding-consent",
        component: OnboardingConsent,
      },
      {
        path: "/onboarding/placement",
        name: "onboarding-placement",
        component: OnboardingPlacement,
      },
    ],
  });
  const wrapper = mount(RouterView, {
    global: { plugins: [router] },
  });
  await router.isReady();
  if (router.currentRoute.value.name !== "onboarding-consent") {
    await router.replace({ name: "onboarding-consent" });
  }
  await flushPromises();
  await nextTick();
  return { wrapper, router, quit };
}

describe("OnboardingConsent", () => {
  beforeEach(() => {
    mockBridges();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("under-16 shows hard-block and quit CTA invokes desktop.quit", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, { ...INTAKE_DONE, age: 15 }));
    const { wrapper, quit, router } = await mountConsent(fetchMock);
    expect(wrapper.find("[data-testid=\"age-hard-block\"]").exists()).toBe(true);
    expect(wrapper.find("[data-testid=\"consent-form\"]").exists()).toBe(false);
    await wrapper.get("[data-testid=\"quit-button\"]").trigger("click");
    expect(quit).toHaveBeenCalledOnce();
    expect(router.currentRoute.value.name).toBe("onboarding-consent");
    wrapper.unmount();
  });

  it("null age hard-blocks like under-16", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, { ...INTAKE_DONE, age: null }));
    const { wrapper } = await mountConsent(fetchMock);
    expect(wrapper.find("[data-testid=\"age-hard-block\"]").exists()).toBe(true);
    expect(wrapper.get("[data-testid=\"quit-button\"]").text()).toBe(
      "Закрыть приложение",
    );
    wrapper.unmount();
  });

  it("missing required consents blocks Далее without PATCH", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, INTAKE_DONE));
    const { wrapper } = await mountConsent(fetchMock);
    await wrapper.get("[data-testid=\"next-button\"]").trigger("click");
    await flushPromises();
    expect(wrapper.get("[data-testid=\"validation-error\"]").text()).toContain(
      "обязательные",
    );
    const patchCalls = fetchMock.mock.calls.filter(
      (c) => (c[1] as RequestInit | undefined)?.method === "PATCH",
    );
    expect(patchCalls).toHaveLength(0);
    expect(wrapper.find("[data-testid=\"consent-form\"]").exists()).toBe(true);
    wrapper.unmount();
  });

  it("accepts required (Telegram optional) and hands off to placement stub", async () => {
    const completed = {
      ...INTAKE_DONE,
      consent_mic: true,
      consent_telegram: false,
      consent_ai: true,
      consent_privacy: true,
      consent_complete: true,
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(200, INTAKE_DONE))
      .mockResolvedValueOnce(jsonResponse(200, completed));
    const { wrapper, router } = await mountConsent(fetchMock);

    await wrapper.get('[data-testid="consent-mic"] input').setValue(true);
    await wrapper.get('[data-testid="consent-ai"] input').setValue(true);
    await wrapper.get('[data-testid="consent-privacy"] input').setValue(true);
    await wrapper.get("[data-testid=\"next-button\"]").trigger("click");
    await flushPromises();
    await nextTick();

    const patchCall = fetchMock.mock.calls.find(
      (c) => (c[1] as RequestInit | undefined)?.method === "PATCH",
    );
    expect(JSON.parse(String((patchCall![1] as RequestInit).body))).toEqual({
      consent_mic: true,
      consent_telegram: false,
      consent_ai: true,
      consent_privacy: true,
      consent_complete: true,
    });
    expect(router.currentRoute.value.name).toBe("onboarding-placement");
    expect(
      wrapper.find("[data-testid=\"onboarding-placement\"]").exists(),
    ).toBe(true);
    wrapper.unmount();
  });

  it("does not re-ask age on consent form", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, INTAKE_DONE));
    const { wrapper } = await mountConsent(fetchMock);
    expect(wrapper.find('input[type="number"]').exists()).toBe(false);
    expect(wrapper.text()).toContain("не спрашивается");
    expect(wrapper.text()).toContain("повторного прослушивания");
    expect(wrapper.text()).toContain("не сертифицированный");
    expect(wrapper.text()).toContain("фамилия");
    wrapper.unmount();
  });

  it("API 422 on complete stays on consent with error", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(200, INTAKE_DONE))
      .mockResolvedValueOnce(
        jsonResponse(422, {
          code: "consent_incomplete",
          message: "consent_complete requires consent_ai",
          retryable: false,
        }),
      );
    const { wrapper, router } = await mountConsent(fetchMock);
    await wrapper.get('[data-testid="consent-mic"] input').setValue(true);
    await wrapper.get('[data-testid="consent-ai"] input').setValue(true);
    await wrapper.get('[data-testid="consent-privacy"] input').setValue(true);
    await wrapper.get("[data-testid=\"next-button\"]").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.name).toBe("onboarding-consent");
    expect(wrapper.get("[data-testid=\"save-error\"]").text()).toContain(
      "consent_complete",
    );
    wrapper.unmount();
  });

  it("hydrates checkboxes from GET mid-consent", async () => {
    const mid = {
      ...INTAKE_DONE,
      consent_mic: true,
      consent_telegram: true,
      consent_ai: false,
      consent_privacy: true,
    };
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, mid));
    const { wrapper } = await mountConsent(fetchMock);
    expect(
      (wrapper.get('[data-testid="consent-mic"] input').element as HTMLInputElement)
        .checked,
    ).toBe(true);
    expect(
      (
        wrapper.get('[data-testid="consent-telegram"] input')
          .element as HTMLInputElement
      ).checked,
    ).toBe(true);
    expect(
      (wrapper.get('[data-testid="consent-ai"] input').element as HTMLInputElement)
        .checked,
    ).toBe(false);
    expect(
      (
        wrapper.get('[data-testid="consent-privacy"] input')
          .element as HTMLInputElement
      ).checked,
    ).toBe(true);
    wrapper.unmount();
  });

  it("age=16 shows consent form not hard-block", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, { ...INTAKE_DONE, age: 16 }));
    const { wrapper } = await mountConsent(fetchMock);
    expect(wrapper.find("[data-testid=\"consent-form\"]").exists()).toBe(true);
    expect(wrapper.find("[data-testid=\"age-hard-block\"]").exists()).toBe(false);
    wrapper.unmount();
  });

  it("quit CTA shows Russian error when desktop.quit missing", async () => {
    Object.defineProperty(window, "teacher", {
      configurable: true,
      value: {
        getAuth: vi.fn().mockResolvedValue(RUNNING_AUTH),
        retry: vi.fn().mockResolvedValue(RUNNING_AUTH),
        onStatusChange: vi.fn().mockReturnValue(() => undefined),
      },
    });
    Object.defineProperty(window, "desktop", {
      configurable: true,
      value: { scaffold: "1.1" },
    });
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, { ...INTAKE_DONE, age: 15 }));
    vi.stubGlobal("fetch", fetchMock);
    const router = createRouter({
      history: createWebHashHistory(),
      routes: [
        {
          path: "/onboarding/consent",
          name: "onboarding-consent",
          component: OnboardingConsent,
        },
      ],
    });
    window.location.hash = "#/onboarding/consent";
    const wrapper = mount(RouterView, { global: { plugins: [router] } });
    await router.isReady();
    await flushPromises();
    await nextTick();
    await wrapper.get("[data-testid=\"quit-button\"]").trigger("click");
    expect(wrapper.get("[data-testid=\"quit-error\"]").text()).toContain("трея");
    wrapper.unmount();
  });
});

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { nextTick } from "vue";
import { createRouter, createWebHashHistory, type Router } from "vue-router";
import { RouterView } from "vue-router";
import OnboardingWizard from "./OnboardingWizard.vue";
import OnboardingConsent from "./OnboardingConsent.vue";
import type { LearnerProfile } from "../services/teacherClient";

const RUNNING_AUTH = {
  state: "running" as const,
  base_url: "http://127.0.0.1:8765",
  bearer: "tok-123",
};

const FRESH_LEARNER: LearnerProfile = {
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
  intake_step: "greeting",
  consent_mic: false,
  consent_telegram: false,
  consent_ai: false,
  consent_privacy: false,
  consent_complete: false,
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

async function mountWizard(fetchImpl: ReturnType<typeof vi.fn>): Promise<{
  wrapper: ReturnType<typeof mount>;
  router: Router;
  fetchMock: ReturnType<typeof vi.fn>;
}> {
  vi.stubGlobal("fetch", fetchImpl);
  window.location.hash = "#/onboarding";
  const router = createRouter({
    history: createWebHashHistory(),
    routes: [
      { path: "/", redirect: "/onboarding" },
      { path: "/onboarding", name: "onboarding", component: OnboardingWizard },
      {
        path: "/onboarding/consent",
        name: "onboarding-consent",
        component: OnboardingConsent,
      },
    ],
  });
  const wrapper = mount(RouterView, {
    global: { plugins: [router] },
  });
  await router.isReady();
  if (router.currentRoute.value.name !== "onboarding") {
    await router.replace({ name: "onboarding" });
  }
  await flushPromises();
  await nextTick();
  return { wrapper, router, fetchMock: fetchImpl };
}

describe("OnboardingWizard", () => {
  beforeEach(() => {
    mockTeacherBridge();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("hydrates greeting and PATCHes on Далее", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(200, FRESH_LEARNER))
      .mockResolvedValueOnce(
        jsonResponse(200, {
          ...FRESH_LEARNER,
          address_as: "Алекс",
          age: 28,
          intake_step: "goals",
        }),
      );
    const { wrapper } = await mountWizard(fetchMock);
    expect(wrapper.find("[data-testid=\"step-greeting\"]").exists()).toBe(true);

    await wrapper.get("[data-testid=\"address-as-input\"]").setValue("Алекс");
    await wrapper.get("[data-testid=\"age-input\"]").setValue("28");
    await wrapper.get("[data-testid=\"next-button\"]").trigger("click");
    await flushPromises();

    const patchCall = fetchMock.mock.calls.find(
      (c) => (c[1] as RequestInit | undefined)?.method === "PATCH",
    );
    expect(patchCall).toBeTruthy();
    expect(patchCall![0]).toBe("http://127.0.0.1:8765/learner");
    expect(JSON.parse(String((patchCall![1] as RequestInit).body))).toEqual({
      address_as: "Алекс",
      age: 28,
      intake_step: "goals",
    });
    expect(wrapper.find("[data-testid=\"step-goals\"]").exists()).toBe(true);
    wrapper.unmount();
  });

  it("resumes mid-wizard at goals with hydrated fields", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        ...FRESH_LEARNER,
        address_as: "Саша",
        age: 30,
        intake_step: "goals",
        goals: ["Учёба"],
        desired_outcome: ["Свой результат"],
      }),
    );
    const { wrapper } = await mountWizard(fetchMock);
    expect(wrapper.find("[data-testid=\"step-goals\"]").exists()).toBe(true);
    expect(
      wrapper
        .findAll(".chip")
        .some((b) => b.text() === "Учёба" && b.classes().includes("selected")),
    ).toBe(true);
    expect(
      (wrapper.get("[data-testid=\"outcome-other\"]").element as HTMLInputElement)
        .value,
    ).toBe("Свой результат");
    wrapper.unmount();
  });

  it("blocks schedule advance with zero slots and clear Russian copy", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        ...FRESH_LEARNER,
        address_as: "Саша",
        age: 30,
        intake_step: "schedule",
        lesson_duration_minutes: 45,
        timezone: "Europe/Moscow",
        weekly_slots: [],
      }),
    );
    const { wrapper } = await mountWizard(fetchMock);
    expect(wrapper.find("[data-testid=\"step-schedule\"]").exists()).toBe(true);
    await wrapper.get("[data-testid=\"next-button\"]").trigger("click");
    await flushPromises();
    expect(wrapper.get("[data-testid=\"validation-error\"]").text()).toContain(
      "хотя бы один слот",
    );
    const patchCalls = fetchMock.mock.calls.filter(
      (c) => (c[1] as RequestInit | undefined)?.method === "PATCH",
    );
    expect(patchCalls).toHaveLength(0);
    wrapper.unmount();
  });

  it("schedule save hands off to consent", async () => {
    const completed = {
      ...FRESH_LEARNER,
      address_as: "Саша",
      age: 30,
      intake_step: "complete" as const,
      lesson_duration_minutes: 45,
      timezone: "Europe/Moscow",
      weekly_slots: [{ weekday: 0, start_minute: 540 }],
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse(200, {
          ...FRESH_LEARNER,
          address_as: "Саша",
          age: 30,
          intake_step: "schedule",
          lesson_duration_minutes: 45,
          timezone: "Europe/Moscow",
          weekly_slots: [],
        }),
      )
      .mockResolvedValueOnce(jsonResponse(200, completed))
      .mockResolvedValue(jsonResponse(200, completed));
    const { wrapper, router } = await mountWizard(fetchMock);
    await wrapper.get('[data-testid="half-0-9-00"]').trigger("click");
    await wrapper.get("[data-testid=\"next-button\"]").trigger("click");
    await flushPromises();
    const patchCall = fetchMock.mock.calls.find(
      (c) => (c[1] as RequestInit | undefined)?.method === "PATCH",
    );
    expect(JSON.parse(String((patchCall![1] as RequestInit).body))).toEqual({
      timezone: "Europe/Moscow",
      weekly_slots: [{ weekday: 0, start_minute: 540 }],
      intake_step: "complete",
    });
    expect(router.currentRoute.value.name).toBe("onboarding-consent");
    expect(wrapper.find("[data-testid=\"onboarding-consent\"]").exists()).toBe(
      true,
    );
    wrapper.unmount();
  });

  it("toggles :00 and :30 halves and shows both chips", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        ...FRESH_LEARNER,
        address_as: "Саша",
        age: 30,
        intake_step: "schedule",
        lesson_duration_minutes: 45,
        timezone: "Europe/Moscow",
        weekly_slots: [],
      }),
    );
    const { wrapper } = await mountWizard(fetchMock);
    await wrapper.get('[data-testid="half-0-9-00"]').trigger("click");
    await wrapper.get('[data-testid="half-0-9-30"]').trigger("click");
    await flushPromises();
    expect(
      wrapper.get('[data-testid="half-0-9-00"]').attributes("aria-pressed"),
    ).toBe("true");
    expect(
      wrapper.get('[data-testid="half-0-9-30"]').attributes("aria-pressed"),
    ).toBe("true");
    expect(wrapper.find(".chip-top").exists()).toBe(true);
    expect(wrapper.find(".chip-mid").exists()).toBe(true);
    wrapper.unmount();
  });

  it("keeps prior :30 without snap notice", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        ...FRESH_LEARNER,
        address_as: "Саша",
        age: 30,
        intake_step: "schedule",
        lesson_duration_minutes: 45,
        timezone: "Europe/Moscow",
        weekly_slots: [{ weekday: 0, start_minute: 570 }],
      }),
    );
    const { wrapper } = await mountWizard(fetchMock);
    expect(
      wrapper.get('[data-testid="half-0-9-30"]').attributes("aria-pressed"),
    ).toBe("true");
    expect(wrapper.find("[data-testid=\"snap-notice\"]").exists()).toBe(false);
    wrapper.unmount();
  });

  it("fine-snaps 09:15 → 09:00 and shows RU notice", async () => {
    const completed = {
      ...FRESH_LEARNER,
      address_as: "Саша",
      age: 30,
      intake_step: "complete" as const,
      lesson_duration_minutes: 45,
      timezone: "Europe/Moscow",
      weekly_slots: [{ weekday: 0, start_minute: 540 }],
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse(200, {
          ...FRESH_LEARNER,
          address_as: "Саша",
          age: 30,
          intake_step: "schedule",
          lesson_duration_minutes: 45,
          timezone: "Europe/Moscow",
          weekly_slots: [{ weekday: 0, start_minute: 555 }],
        }),
      )
      .mockResolvedValueOnce(jsonResponse(200, completed))
      .mockResolvedValue(jsonResponse(200, completed));
    const { wrapper } = await mountWizard(fetchMock);
    await flushPromises();
    expect(
      wrapper.get('[data-testid="half-0-9-00"]').attributes("aria-pressed"),
    ).toBe("true");
    expect(wrapper.get("[data-testid=\"snap-notice\"]").text()).toContain(
      "округлено до получаса",
    );
    await wrapper.get("[data-testid=\"next-button\"]").trigger("click");
    await flushPromises();
    const patchCall = fetchMock.mock.calls.find(
      (c) => (c[1] as RequestInit | undefined)?.method === "PATCH",
    );
    expect(JSON.parse(String((patchCall![1] as RequestInit).body))).toEqual({
      timezone: "Europe/Moscow",
      weekly_slots: [{ weekday: 0, start_minute: 540 }],
      intake_step: "complete",
    });
    wrapper.unmount();
  });

  it("fine-snaps 09:45 → 09:30 and coalesces 09:10 with 09:00", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        ...FRESH_LEARNER,
        address_as: "Саша",
        age: 30,
        intake_step: "schedule",
        lesson_duration_minutes: 45,
        timezone: "Europe/Moscow",
        weekly_slots: [
          { weekday: 0, start_minute: 585 },
          { weekday: 1, start_minute: 550 },
          { weekday: 1, start_minute: 540 },
        ],
      }),
    );
    const { wrapper } = await mountWizard(fetchMock);
    await flushPromises();
    expect(
      wrapper.get('[data-testid="half-0-9-30"]').attributes("aria-pressed"),
    ).toBe("true");
    expect(
      wrapper.get('[data-testid="half-1-9-00"]').attributes("aria-pressed"),
    ).toBe("true");
    expect(
      wrapper.get('[data-testid="half-1-9-30"]').attributes("aria-pressed"),
    ).toBe("false");
    expect(wrapper.find("[data-testid=\"snap-notice\"]").exists()).toBe(true);
    wrapper.unmount();
  });

  it("INITIAL_VIEW scrolls in-band by default and evening 22:30 into view", async () => {
    const inBand = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        ...FRESH_LEARNER,
        address_as: "Саша",
        age: 30,
        intake_step: "schedule",
        lesson_duration_minutes: 45,
        timezone: "Europe/Moscow",
        weekly_slots: [],
      }),
    );
    const { wrapper: emptyWrapper } = await mountWizard(inBand);
    const emptyScroll = emptyWrapper.get(
      '[data-testid="schedule-grid-scroll"]',
    ).element as HTMLElement;
    expect(emptyScroll.scrollTop).toBe(7 * 52);
    emptyWrapper.unmount();

    const evening = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        ...FRESH_LEARNER,
        address_as: "Саша",
        age: 30,
        intake_step: "schedule",
        lesson_duration_minutes: 45,
        timezone: "Europe/Moscow",
        weekly_slots: [{ weekday: 0, start_minute: 1350 }],
      }),
    );
    const { wrapper: eveningWrapper } = await mountWizard(evening);
    await flushPromises();
    const eveningScroll = eveningWrapper.get(
      '[data-testid="schedule-grid-scroll"]',
    ).element as HTMLElement;
    expect(eveningScroll.scrollTop).toBe(22 * 52);
    expect(
      eveningWrapper
        .get('[data-testid="half-0-22-30"]')
        .attributes("aria-pressed"),
    ).toBe("true");
    eveningWrapper.unmount();
  });

  it("goals step PATCHes selected chips and advances", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse(200, {
          ...FRESH_LEARNER,
          address_as: "Саша",
          age: 30,
          intake_step: "goals",
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse(200, {
          ...FRESH_LEARNER,
          address_as: "Саша",
          age: 30,
          goals: ["Учёба"],
          desired_outcome: ["Уверенный разговор"],
          intake_step: "interests",
        }),
      );
    const { wrapper } = await mountWizard(fetchMock);
    const goalChip = wrapper.findAll(".chip").find((b) => b.text() === "Учёба");
    const outcomeChip = wrapper
      .findAll(".chip")
      .find((b) => b.text() === "Уверенный разговор");
    await goalChip!.trigger("click");
    await outcomeChip!.trigger("click");
    await wrapper.get("[data-testid=\"next-button\"]").trigger("click");
    await flushPromises();
    const patchCall = fetchMock.mock.calls.find(
      (c) => (c[1] as RequestInit | undefined)?.method === "PATCH",
    );
    expect(JSON.parse(String((patchCall![1] as RequestInit).body))).toEqual({
      goals: ["Учёба"],
      desired_outcome: ["Уверенный разговор"],
      intake_step: "interests",
    });
    expect(wrapper.find("[data-testid=\"step-interests\"]").exists()).toBe(true);
    wrapper.unmount();
  });

  it("interests step PATCHes chips and advances", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse(200, {
          ...FRESH_LEARNER,
          address_as: "Саша",
          age: 30,
          intake_step: "interests",
          goals: ["Учёба"],
          desired_outcome: ["Уверенный разговор"],
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse(200, {
          ...FRESH_LEARNER,
          address_as: "Саша",
          age: 30,
          interests: ["Технологии"],
          emphasis: ["Говорение"],
          intake_step: "duration",
        }),
      );
    const { wrapper } = await mountWizard(fetchMock);
    await wrapper
      .findAll(".chip")
      .find((b) => b.text() === "Технологии")!
      .trigger("click");
    await wrapper
      .findAll(".chip")
      .find((b) => b.text() === "Говорение")!
      .trigger("click");
    await wrapper.get("[data-testid=\"next-button\"]").trigger("click");
    await flushPromises();
    const patchCall = fetchMock.mock.calls.find(
      (c) => (c[1] as RequestInit | undefined)?.method === "PATCH",
    );
    expect(JSON.parse(String((patchCall![1] as RequestInit).body))).toEqual({
      interests: ["Технологии"],
      emphasis: ["Говорение"],
      intake_step: "duration",
    });
    expect(wrapper.find("[data-testid=\"step-duration\"]").exists()).toBe(true);
    wrapper.unmount();
  });

  it("duration step PATCHes minutes and advances", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse(200, {
          ...FRESH_LEARNER,
          address_as: "Саша",
          age: 30,
          intake_step: "duration",
          goals: ["Учёба"],
          desired_outcome: ["Уверенный разговор"],
          interests: ["Технологии"],
          emphasis: ["Говорение"],
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse(200, {
          ...FRESH_LEARNER,
          address_as: "Саша",
          age: 30,
          lesson_duration_minutes: 45,
          intake_step: "schedule",
        }),
      );
    const { wrapper } = await mountWizard(fetchMock);
    await wrapper
      .findAll(".chip")
      .find((b) => b.text() === "45 мин")!
      .trigger("click");
    await wrapper.get("[data-testid=\"next-button\"]").trigger("click");
    await flushPromises();
    const patchCall = fetchMock.mock.calls.find(
      (c) => (c[1] as RequestInit | undefined)?.method === "PATCH",
    );
    expect(JSON.parse(String((patchCall![1] as RequestInit).body))).toEqual({
      lesson_duration_minutes: 45,
      intake_step: "schedule",
    });
    expect(wrapper.find("[data-testid=\"step-schedule\"]").exists()).toBe(true);
    wrapper.unmount();
  });

  it("surfaces teacher error on save without advancing", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(200, FRESH_LEARNER))
      .mockResolvedValueOnce(
        jsonResponse(401, {
          code: "unauthorized",
          message: "Missing or invalid authentication token",
          retryable: false,
        }),
      );
    const { wrapper } = await mountWizard(fetchMock);
    await wrapper.get("[data-testid=\"address-as-input\"]").setValue("Алекс");
    await wrapper.get("[data-testid=\"age-input\"]").setValue("28");
    await wrapper.get("[data-testid=\"next-button\"]").trigger("click");
    await flushPromises();
    expect(wrapper.get("[data-testid=\"save-error\"]").text()).toContain(
      "Missing or invalid",
    );
    expect(wrapper.find("[data-testid=\"step-greeting\"]").exists()).toBe(true);
    wrapper.unmount();
  });
});

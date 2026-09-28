import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { nextTick } from "vue";
import { createRouter, createWebHashHistory, type Router } from "vue-router";
import { RouterView } from "vue-router";
import SettingsView from "./SettingsView.vue";

const RUNNING_AUTH = {
  state: "running" as const,
  base_url: "http://127.0.0.1:8765",
  bearer: "test-bearer-token",
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
} {
  const status = { ...RUNNING_AUTH, ...overrides };
  const getAuth = vi.fn().mockResolvedValue(status);
  const retry = vi.fn().mockResolvedValue(status);
  Object.defineProperty(window, "teacher", {
    configurable: true,
    value: {
      getAuth,
      retry,
      onStatusChange: vi.fn().mockReturnValue(() => undefined),
    },
  });
  return { getAuth, retry };
}

async function mountSettings(): Promise<{
  wrapper: ReturnType<typeof mount>;
  router: Router;
}> {
  const router = createRouter({
    history: createWebHashHistory(),
    routes: [
      { path: "/", redirect: "/settings" },
      { path: "/settings", name: "settings", component: SettingsView },
      {
        path: "/calendar",
        name: "calendar",
        component: { template: "<div>calendar</div>" },
      },
    ],
  });
  window.location.hash = "#/settings";
  // Mount through <router-view> (not the bare component) so SettingsView has
  // an active route record for `onBeforeRouteLeave` to attach to.
  const wrapper = mount(RouterView, {
    global: { plugins: [router] },
  });
  await router.isReady();
  await flushPromises();
  await nextTick();
  return { wrapper, router };
}

describe("SettingsView — sections shell + explicit save", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows documented stub chrome for Telegram/Voice/Schedule/Goals", async () => {
    mockTeacherBridge();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(200, { configured: false })),
    );
    const { wrapper } = await mountSettings();

    expect(wrapper.text()).toContain("TELEGRAM");
    expect(wrapper.text()).toContain("не привязан");
    const telegramBtn = wrapper.get("button:not([disabled]), button[disabled]");
    void telegramBtn;
    const bindBtn = wrapper
      .findAll("button")
      .find((b) => b.text() === "Привязать");
    expect(bindBtn?.attributes("disabled")).toBeDefined();

    expect(wrapper.text()).toContain("ГОЛОС");
    expect(wrapper.text()).toContain("РАСПИСАНИЕ И ДЛИТЕЛЬНОСТЬ");
    const changeBtn = wrapper
      .findAll("button")
      .find((b) => b.text() === "Изменить");
    expect(changeBtn?.attributes("disabled")).toBeDefined();

    expect(wrapper.text()).toContain("ЦЕЛИ И АКЦЕНТЫ");
    expect(wrapper.text()).toContain("LLM / API");
    wrapper.unmount();
  });

  it("loads masked configured status; field always starts empty", async () => {
    mockTeacherBridge();
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, { configured: true }));
    vi.stubGlobal("fetch", fetchMock);
    const { wrapper } = await mountSettings();

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8765/config/llm",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer test-bearer-token",
        }),
      }),
    );
    expect(wrapper.find('[data-testid="llm-configured-hint"]').exists()).toBe(
      true,
    );
    const input = wrapper.get("#llm-api-key").element as HTMLInputElement;
    expect(input.value).toBe("");
    wrapper.unmount();
  });

  it("rejects an empty/whitespace save client-side without calling PUT (no autosave)", async () => {
    mockTeacherBridge();
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(200, { configured: false }));
    vi.stubGlobal("fetch", fetchMock);
    const { wrapper } = await mountSettings();

    await wrapper.get("#llm-api-key").setValue("   ");
    await wrapper.get('[data-testid="save-llm-button"]').trigger("click");
    await nextTick();

    expect(wrapper.find('[data-testid="validation-error"]').exists()).toBe(
      true,
    );
    expect(fetchMock).toHaveBeenCalledTimes(1); // only the initial GET; no PUT
    wrapper.unmount();
  });

  it("saves a non-empty key via PUT, masks the field again, and never autosaves on keystroke", async () => {
    mockTeacherBridge();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(200, { configured: false })) // initial GET
      .mockResolvedValueOnce(jsonResponse(200, { configured: true })); // PUT
    vi.stubGlobal("fetch", fetchMock);
    const { wrapper } = await mountSettings();

    const input = wrapper.get("#llm-api-key");
    await input.setValue("sk-test-key-0001");
    // Typing alone must never call PUT.
    expect(fetchMock).toHaveBeenCalledTimes(1);

    await wrapper.get('[data-testid="save-llm-button"]').trigger("click");
    await flushPromises();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    const [, putInit] = fetchMock.mock.calls[1] as [string, RequestInit];
    expect(putInit.method).toBe("PUT");
    expect(putInit.body).toBe(
      JSON.stringify({ llm_api_key: "sk-test-key-0001" }),
    );
    expect((input.element as HTMLInputElement).value).toBe("");
    expect(wrapper.find('[data-testid="llm-configured-hint"]').exists()).toBe(
      true,
    );
    wrapper.unmount();
  });

  it("shows error + retry when save hits teacher-down/401; input is preserved, no silent success", async () => {
    mockTeacherBridge();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(200, { configured: false })) // initial GET
      .mockResolvedValueOnce(
        jsonResponse(401, {
          code: "unauthorized",
          message: "Нет доступа",
          retryable: false,
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    const { wrapper } = await mountSettings();

    await wrapper.get("#llm-api-key").setValue("sk-test-key-0002");
    await wrapper.get('[data-testid="save-llm-button"]').trigger("click");
    await flushPromises();

    expect(wrapper.find('[data-testid="save-error"]').text()).toContain(
      "Нет доступа",
    );
    expect(
      (wrapper.get("#llm-api-key").element as HTMLInputElement).value,
    ).toBe("sk-test-key-0002");
    // Retry = re-click «Сохранить»: button must be usable again after failure.
    expect(
      wrapper.get('[data-testid="save-llm-button"]').attributes("disabled"),
    ).toBeUndefined();
    fetchMock.mockResolvedValueOnce(jsonResponse(200, { configured: true }));
    await wrapper.get('[data-testid="save-llm-button"]').trigger("click");
    await flushPromises();
    expect(fetchMock).toHaveBeenCalledTimes(3); // GET + failed PUT + retry PUT
    wrapper.unmount();
  });

  it("blocks leave while a save PUT is in flight", async () => {
    mockTeacherBridge();
    let release!: (value: Response) => void;
    const hungPut = new Promise<Response>((resolve) => {
      release = resolve;
    });
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(200, { configured: false }))
      .mockImplementationOnce(() => hungPut);
    vi.stubGlobal("fetch", fetchMock);
    const confirmSpy = vi.spyOn(window, "confirm");
    const { wrapper, router } = await mountSettings();

    await wrapper.get("#llm-api-key").setValue("sk-in-flight");
    void wrapper.get('[data-testid="save-llm-button"]').trigger("click");
    await nextTick();

    await router.push({ name: "calendar" });
    await flushPromises();
    expect(confirmSpy).not.toHaveBeenCalled();
    expect(router.currentRoute.value.name).toBe("settings");

    release(jsonResponse(200, { configured: true }));
    await flushPromises();
    wrapper.unmount();
  });

  it("LAUNCH_FAILURE_UI: retry recovers to running+bearer, clears the banner, and fetches LLM status", async () => {
    const getAuth = vi
      .fn()
      .mockResolvedValue({
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
      .mockResolvedValue(jsonResponse(200, { configured: false }));
    vi.stubGlobal("fetch", fetchMock);
    const { wrapper } = await mountSettings();

    const banner = wrapper.find('[data-testid="launch-failure-banner"]');
    expect(banner.exists()).toBe(true);
    expect(banner.text()).toContain("Учитель не запущен");
    expect(
      wrapper.get('[data-testid="save-llm-button"]').attributes("disabled"),
    ).toBeDefined();
    expect(fetchMock).not.toHaveBeenCalled();

    await wrapper
      .get('[data-testid="launch-failure-banner"] button')
      .trigger("click");
    await flushPromises();

    expect(retry).toHaveBeenCalledTimes(1);
    expect(wrapper.find('[data-testid="launch-failure-banner"]').exists()).toBe(
      false,
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8765/config/llm",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer test-bearer-token",
        }),
      }),
    );
    wrapper.unmount();
  });

  it("onStatusChange updates auth and loads LLM status once the teacher flips to running", async () => {
    let statusCallback: ((status: typeof RUNNING_AUTH) => void) | undefined;
    const getAuth = vi
      .fn()
      .mockResolvedValue({
        state: "error",
        base_url: "",
        bearer: null,
        message: "Учитель не запущен",
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
      .mockResolvedValue(jsonResponse(200, { configured: true }));
    vi.stubGlobal("fetch", fetchMock);
    const { wrapper } = await mountSettings();

    expect(wrapper.find('[data-testid="launch-failure-banner"]').exists()).toBe(
      true,
    );
    expect(statusCallback).toBeDefined();

    statusCallback?.({ ...RUNNING_AUTH });
    await flushPromises();

    expect(wrapper.find('[data-testid="launch-failure-banner"]').exists()).toBe(
      false,
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8765/config/llm",
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer test-bearer-token",
        }),
      }),
    );
    expect(wrapper.find('[data-testid="llm-configured-hint"]').exists()).toBe(
      true,
    );
    wrapper.unmount();
  });

  it("shows load-error when the initial LLM status GET fails", async () => {
    mockTeacherBridge();
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          jsonResponse(500, {
            code: "server_error",
            message: "Сбой сервера",
            retryable: true,
          }),
        ),
    );
    const { wrapper } = await mountSettings();

    expect(wrapper.find('[data-testid="load-error"]').text()).toContain(
      "Сбой сервера",
    );
    wrapper.unmount();
  });

  it("leave-dirty: confirms before navigating away with unsaved LLM edits; stays on cancel", async () => {
    mockTeacherBridge();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(200, { configured: false })),
    );
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(false);
    const { wrapper, router } = await mountSettings();

    await wrapper.get("#llm-api-key").setValue("sk-unsaved");
    await router.push({ name: "calendar" });
    await flushPromises();

    expect(confirmSpy).toHaveBeenCalledTimes(1);
    expect(router.currentRoute.value.name).toBe("settings");
    expect(
      (wrapper.get("#llm-api-key").element as HTMLInputElement).value,
    ).toBe("sk-unsaved");
    wrapper.unmount();
  });

  it("leave-dirty: navigates away after confirm; never silently discards without confirmation", async () => {
    mockTeacherBridge();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(200, { configured: false })),
    );
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    const { wrapper, router } = await mountSettings();

    await wrapper.get("#llm-api-key").setValue("sk-unsaved");
    await router.push({ name: "calendar" });
    await flushPromises();

    expect(confirmSpy).toHaveBeenCalledTimes(1);
    expect(router.currentRoute.value.name).toBe("calendar");
    wrapper.unmount();
  });

  it("leaves without a confirm prompt when there are no unsaved edits", async () => {
    mockTeacherBridge();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(200, { configured: false })),
    );
    const confirmSpy = vi.spyOn(window, "confirm");
    const { wrapper, router } = await mountSettings();

    await router.push({ name: "calendar" });
    await flushPromises();

    expect(confirmSpy).not.toHaveBeenCalled();
    expect(router.currentRoute.value.name).toBe("calendar");
    wrapper.unmount();
  });
});

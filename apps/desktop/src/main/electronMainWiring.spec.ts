/**
 * Closes the 1.6 verification gaps for HOST_SURVIVAL + AUTH_BRIDGE without a
 * full Electron main harness (unavailable in this sandbox). Static scans catch
 * index.ts wiring regressions; mocked preload import executes the bridge surface.
 */
import { describe, expect, it, vi } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import {
  DESKTOP_QUIT_CHANNEL,
  TEACHER_GET_AUTH_CHANNEL,
  TEACHER_RETRY_CHANNEL,
  TEACHER_STATUS_CHANNEL,
} from "../shared/ipcChannels";

const mainSrc = readFileSync(join(__dirname, "index.ts"), "utf8");
const preloadSrc = readFileSync(join(__dirname, "../preload/index.ts"), "utf8");

describe("HOST_SURVIVAL main wiring (static)", () => {
  it("wires close→hide, window-all-closed policy, tray/desktop quit, before-quit stop-owned", () => {
    expect(mainSrc).toMatch(/windowCloseAction\s*\(\s*isQuitting\s*\)/);
    expect(mainSrc).toMatch(/\.on\(\s*["']close["']/);
    expect(mainSrc).toMatch(/win\.hide\s*\(/);

    expect(mainSrc).toMatch(
      /app\.on\(\s*["']window-all-closed["'][\s\S]*?shouldQuitOnWindowAllClosed\s*\(/,
    );

    expect(mainSrc).toMatch(/beginExplicitQuit\s*\(/);
    expect(mainSrc).toMatch(/label:\s*["']Выход["'][\s\S]*?requestQuit\s*\(/);
    expect(mainSrc).toMatch(
      /ipcMain\.handle\(\s*DESKTOP_QUIT_CHANNEL[\s\S]*?requestQuit\s*\(/,
    );

    expect(mainSrc).toMatch(
      /app\.on\(\s*["']before-quit["'][\s\S]*?quitTeacherAction\s*\(\s*teacherHost\.ownsChildProcess\s*\(\s*\)\s*\)/,
    );
    expect(mainSrc).toMatch(
      /quitTeacherAction[\s\S]*?===\s*["']stop-owned["'][\s\S]*?teacherHost\.stop\s*\(/,
    );
  });
});

describe("AUTH_BRIDGE main/preload wiring", () => {
  it("main registers get-auth / retry handlers and status push channel", () => {
    expect(mainSrc).toMatch(
      /ipcMain\.handle\(\s*TEACHER_GET_AUTH_CHANNEL\s*,\s*\(\s*\)\s*=>\s*teacherHost\.getStatus\s*\(\s*\)\s*\)/,
    );
    expect(mainSrc).toMatch(
      /ipcMain\.handle\(\s*TEACHER_RETRY_CHANNEL\s*,\s*\(\s*\)\s*=>\s*teacherHost\.start\s*\(\s*\)\s*\)/,
    );
    expect(mainSrc).toMatch(
      /webContents\.send\(\s*TEACHER_STATUS_CHANNEL\s*,/,
    );
  });

  it("preload invokes the same channels and exposes teacher bridge", () => {
    expect(preloadSrc).toMatch(
      /ipcRenderer\.invoke\(\s*TEACHER_GET_AUTH_CHANNEL\b/,
    );
    expect(preloadSrc).toMatch(
      /ipcRenderer\.invoke\(\s*TEACHER_RETRY_CHANNEL\b/,
    );
    expect(preloadSrc).toMatch(
      /ipcRenderer\.on\(\s*TEACHER_STATUS_CHANNEL\b/,
    );
    expect(preloadSrc).toMatch(
      /exposeInMainWorld\(\s*['"]teacher['"]/,
    );
  });

  it("executes preload bridge registration under mocked electron", async () => {
    vi.resetModules();

    const exposeInMainWorld = vi.fn();
    const invoke = vi.fn().mockResolvedValue({
      state: "stopped",
      base_url: "http://127.0.0.1:8765",
      bearer: null,
    });
    const on = vi.fn();
    const removeListener = vi.fn();

    vi.doMock("electron", () => ({
      contextBridge: { exposeInMainWorld },
      ipcRenderer: { invoke, on, removeListener },
    }));

    await import("../preload/index");

    expect(exposeInMainWorld).toHaveBeenCalledWith(
      "desktop",
      expect.objectContaining({
        scaffold: "1.1",
        quit: expect.any(Function),
      }),
    );
    expect(exposeInMainWorld).toHaveBeenCalledWith(
      "teacher",
      expect.objectContaining({
        getAuth: expect.any(Function),
        retry: expect.any(Function),
        onStatusChange: expect.any(Function),
      }),
    );

    const teacherApi = exposeInMainWorld.mock.calls.find(
      (c) => c[0] === "teacher",
    )?.[1] as {
      getAuth: () => Promise<unknown>;
      retry: () => Promise<unknown>;
      onStatusChange: (cb: (s: unknown) => void) => () => void;
    };

    await teacherApi.getAuth();
    expect(invoke).toHaveBeenCalledWith(TEACHER_GET_AUTH_CHANNEL);

    await teacherApi.retry();
    expect(invoke).toHaveBeenCalledWith(TEACHER_RETRY_CHANNEL);

    const unsub = teacherApi.onStatusChange(() => undefined);
    expect(on).toHaveBeenCalledWith(
      TEACHER_STATUS_CHANNEL,
      expect.any(Function),
    );
    unsub();
    expect(removeListener).toHaveBeenCalledWith(
      TEACHER_STATUS_CHANNEL,
      expect.any(Function),
    );

    const desktopApi = exposeInMainWorld.mock.calls.find(
      (c) => c[0] === "desktop",
    )?.[1] as { quit: () => Promise<void> };
    await desktopApi.quit();
    expect(invoke).toHaveBeenCalledWith(DESKTOP_QUIT_CHANNEL);
  });
});

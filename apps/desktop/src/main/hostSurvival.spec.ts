import { describe, expect, it, vi } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import {
  beginExplicitQuit,
  quitTeacherAction,
  shouldQuitOnWindowAllClosed,
  windowCloseAction,
} from "./hostSurvival";
import { DESKTOP_QUIT_CHANNEL } from "../shared/ipcChannels";

describe("hostSurvival — tray-first window/quit policy", () => {
  it("Window close: hides (does not allow close) when not quitting — teacher keeps running", () => {
    expect(windowCloseAction(false)).toBe("hide");
  });

  it("Tray reopen path: explicit quit flag is what allows the window to actually close", () => {
    // Reopen is showMainWindow(); close while !isQuitting still hides.
    expect(windowCloseAction(false)).toBe("hide");
    expect(windowCloseAction(true)).toBe("allow-close");
  });

  it("Explicit quit: stops only an owned (spawned) teacher; leaves attached alone", () => {
    expect(quitTeacherAction(true)).toBe("stop-owned");
    expect(quitTeacherAction(false)).toBe("leave-attached");
  });

  it("window-all-closed never quits the app (tray remains)", () => {
    expect(shouldQuitOnWindowAllClosed()).toBe(false);
  });

  it("beginExplicitQuit sets isQuitting before app.quit (tray + desktop:quit)", () => {
    const order: string[] = [];
    beginExplicitQuit(
      () => order.push("set-quitting"),
      () => order.push("quit"),
    );
    expect(order).toEqual(["set-quitting", "quit"]);
  });

  it("desktop:quit channel is stable for preload/main wiring", () => {
    expect(DESKTOP_QUIT_CHANNEL).toBe("desktop:quit");
    const quit = vi.fn();
    beginExplicitQuit(() => undefined, quit);
    expect(quit).toHaveBeenCalledOnce();
  });

  it("main and preload keep DESKTOP_QUIT_CHANNEL / beginExplicitQuit wired", () => {
    const mainSrc = readFileSync(join(__dirname, "index.ts"), "utf8");
    const preloadSrc = readFileSync(
      join(__dirname, "../preload/index.ts"),
      "utf8",
    );
    expect(mainSrc).toMatch(/import\s*\{[^}]*\bbeginExplicitQuit\b/);
    expect(mainSrc).toMatch(/import\s*\{[^}]*\bDESKTOP_QUIT_CHANNEL\b/);
    expect(mainSrc).toMatch(/ipcMain\.handle\(\s*DESKTOP_QUIT_CHANNEL\b/);
    expect(mainSrc).toMatch(/\bbeginExplicitQuit\s*\(/);
    expect(preloadSrc).toMatch(/import\s*\{[^}]*\bDESKTOP_QUIT_CHANNEL\b/);
    expect(preloadSrc).toMatch(
      /ipcRenderer\.invoke\(\s*DESKTOP_QUIT_CHANNEL\b/,
    );
  });
});

import { describe, expect, it } from "vitest";
import {
  quitTeacherAction,
  shouldQuitOnWindowAllClosed,
  windowCloseAction,
} from "./hostSurvival";

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
});

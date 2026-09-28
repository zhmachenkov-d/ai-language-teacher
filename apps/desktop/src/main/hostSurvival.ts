/**
 * Tray-first host-survival decisions (HOST_SURVIVAL).
 * Kept Electron-free so the I/O matrix rows can be unit-tested.
 */

/** Closing the UI window: hide and keep host unless an explicit quit is in progress. */
export function windowCloseAction(isQuitting: boolean): "hide" | "allow-close" {
  return isQuitting ? "allow-close" : "hide";
}

/**
 * Explicit app quit: stop the teacher only if this host spawned it.
 * An attached external process is left running.
 */
export function quitTeacherAction(
  ownsChildProcess: boolean,
): "stop-owned" | "leave-attached" {
  return ownsChildProcess ? "stop-owned" : "leave-attached";
}

/** `window-all-closed` must never quit — tray keeps the host alive. */
export function shouldQuitOnWindowAllClosed(): boolean {
  return false;
}

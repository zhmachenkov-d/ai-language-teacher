/**
 * IPC channel names shared by main (`ipcMain.handle`/`webContents.send`) and
 * preload (`ipcRenderer.invoke`/`ipcRenderer.on`) so the strings cannot drift
 * between the two sides of the teacher lifecycle bridge.
 */
export const TEACHER_GET_AUTH_CHANNEL = 'teacher:get-auth'
export const TEACHER_RETRY_CHANNEL = 'teacher:retry'
export const TEACHER_STATUS_CHANNEL = 'teacher:status'
/** Explicit app quit — same isQuitting path as tray «Выход». */
export const DESKTOP_QUIT_CHANNEL = 'desktop:quit'

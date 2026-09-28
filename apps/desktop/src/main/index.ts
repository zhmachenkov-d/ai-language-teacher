import { app, BrowserWindow, ipcMain, Menu, nativeImage, Tray } from "electron";
import { join } from "path";
import {
  beginExplicitQuit,
  quitTeacherAction,
  shouldQuitOnWindowAllClosed,
  windowCloseAction,
} from "./hostSurvival";
import { TeacherHost, type TeacherStatus } from "./teacherHost";
import {
  DESKTOP_QUIT_CHANNEL,
  TEACHER_GET_AUTH_CHANNEL,
  TEACHER_RETRY_CHANNEL,
  TEACHER_STATUS_CHANNEL,
} from "../shared/ipcChannels";

// Coral brand mark, 16x16 — tray icon (Design Notes: "Tray: app icon").
const TRAY_ICON_DATA_URL =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAN0lEQVR42mNgoAX435j4HxumSDNRhhDSjNcQYjVjNYRUzRiGjBpABQMojkaqJCSqJGWqZCZSAQBHMcCQn7ZYQAAAAABJRU5ErkJggg==";

function isAllowedDevRendererUrl(raw: string): boolean {
  try {
    const url = new URL(raw);
    if (url.protocol !== "http:" && url.protocol !== "https:") {
      return false;
    }
    return url.hostname === "localhost" || url.hostname === "127.0.0.1";
  } catch {
    return false;
  }
}

let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;
// Tray-first host-survival: window close hides the app; only an explicit
// quit (tray "Выход" or equivalent) is allowed to actually close the window.
let isQuitting = false;

const teacherHost = new TeacherHost({
  onStatus: (status: TeacherStatus) => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send(TEACHER_STATUS_CHANNEL, status);
    }
  },
});

function createWindow(): BrowserWindow {
  const win = new BrowserWindow({
    width: 960,
    height: 640,
    show: true,
    title: "AI Language Teacher",
    webPreferences: {
      preload: join(__dirname, "../preload/index.js"),
      contextIsolation: true,
      nodeIntegration: false,
      // electron-vite preload often needs sandbox off; revisit enabling in Story 1.2
      sandbox: false,
    },
  });

  win.webContents.setWindowOpenHandler(() => ({ action: "deny" }));

  win.webContents.on("will-navigate", (event, url) => {
    // Allow packaged file:// loads; only http(s) must be loopback
    if (url.startsWith("file:")) {
      return;
    }
    if (!isAllowedDevRendererUrl(url)) {
      event.preventDefault();
    }
  });

  // HOST_SURVIVAL: closing the window hides it and keeps the teacher running;
  // it must never stop the teacher solely because the window closed.
  win.on("close", (event) => {
    if (windowCloseAction(isQuitting) === "hide") {
      event.preventDefault();
      win.hide();
    }
  });

  const rendererUrl = process.env["ELECTRON_RENDERER_URL"];
  if (rendererUrl && isAllowedDevRendererUrl(rendererUrl)) {
    win.loadURL(rendererUrl);
  } else {
    win.loadFile(join(__dirname, "../renderer/index.html"));
  }

  return win;
}

function showMainWindow(): void {
  if (mainWindow && !mainWindow.isDestroyed()) {
    if (mainWindow.isMinimized()) {
      mainWindow.restore();
    }
    mainWindow.show();
    mainWindow.focus();
    return;
  }
  mainWindow = createWindow();
  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

function requestQuit(): void {
  beginExplicitQuit(() => {
    isQuitting = true;
  }, () => app.quit());
}

function createTray(): void {
  const icon = nativeImage.createFromDataURL(TRAY_ICON_DATA_URL);
  tray = new Tray(icon);
  tray.setToolTip("AI Language Teacher");
  tray.setContextMenu(
    Menu.buildFromTemplate([
      { label: "Открыть", click: () => showMainWindow() },
      { type: "separator" },
      {
        label: "Выход",
        click: () => requestQuit(),
      },
    ]),
  );
  tray.on("click", () => showMainWindow());
}

ipcMain.handle(TEACHER_GET_AUTH_CHANNEL, () => teacherHost.getStatus());
ipcMain.handle(TEACHER_RETRY_CHANNEL, () => teacherHost.start());
ipcMain.handle(DESKTOP_QUIT_CHANNEL, () => {
  requestQuit();
});

app.whenReady().then(async () => {
  createTray();
  showMainWindow();
  await teacherHost.start();

  app.on("activate", () => {
    showMainWindow();
  });
});

// Tray-first host-survival: never quit here — the teacher (and tray) must
// keep running after the last window closes. Explicit quit is tray-only.
app.on("window-all-closed", () => {
  if (shouldQuitOnWindowAllClosed()) {
    app.quit();
  }
});

app.on("before-quit", () => {
  isQuitting = true;
  // Only stops a process this host spawned; an attached external teacher
  // (e.g. a manually started dev instance) is left running.
  if (quitTeacherAction(teacherHost.ownsChildProcess()) === "stop-owned") {
    teacherHost.stop();
  }
});

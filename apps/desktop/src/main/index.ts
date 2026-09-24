import { app, BrowserWindow } from "electron";
import { join } from "path";

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

function createWindow(): void {
  const mainWindow = new BrowserWindow({
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

  mainWindow.webContents.setWindowOpenHandler(() => ({ action: "deny" }));

  mainWindow.webContents.on("will-navigate", (event, url) => {
    // Allow packaged file:// loads; only http(s) must be loopback
    if (url.startsWith("file:")) {
      return;
    }
    if (!isAllowedDevRendererUrl(url)) {
      event.preventDefault();
    }
  });

  const rendererUrl = process.env["ELECTRON_RENDERER_URL"];
  if (rendererUrl && isAllowedDevRendererUrl(rendererUrl)) {
    mainWindow.loadURL(rendererUrl);
  } else {
    mainWindow.loadFile(join(__dirname, "../renderer/index.html"));
  }
}

app.whenReady().then(() => {
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

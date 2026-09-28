/**
 * Thin-host teacher lifecycle: spawn/attach/stop/status + Config bearer mint.
 *
 * Electron-free by design (only Node builtins) so the decision logic (ATTACH,
 * REMINT, HOST_SURVIVAL) is unit-testable without an Electron runtime. Domain
 * traffic stays HTTP; this module only ever touches the loopback `/health`
 * endpoint and the shared Config secrets file layout — never a second
 * authoritative bearer store.
 */
import { type ChildProcess, spawn as nodeSpawn } from "node:child_process";
import { randomBytes } from "node:crypto";
import {
  chmodSync,
  existsSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import { homedir, platform as nodePlatform } from "node:os";
import { join, resolve as resolvePath } from "node:path";

export const APP_NAME = "ai-language-teacher";
export const SECRET_BEARER_TOKEN = "bearer_token";
export const LOOPBACK_HOST = "127.0.0.1";
export const TEACHER_PORT = 8765;
export const BASE_URL = `http://${LOOPBACK_HOST}:${TEACHER_PORT}`;

export type TeacherState = "starting" | "running" | "stopped" | "error";

export interface TeacherStatus {
  state: TeacherState;
  base_url: string;
  bearer: string | null;
  message?: string;
}

// --- Config data-dir + Bearer secret (mirrors services/teacher FileConfig layout) ---

/** Resolve the shared learner data dir: `TEACHER_DATA_DIR` override → OS app-data default. */
export function resolveDataDir(
  env: NodeJS.ProcessEnv = process.env,
  platformName: NodeJS.Platform = nodePlatform(),
): string {
  const override = env.TEACHER_DATA_DIR;
  if (typeof override === "string" && override.trim()) {
    return resolvePath(override.trim());
  }
  const home = (): string =>
    typeof env.HOME === "string" && env.HOME.trim() ? env.HOME : homedir();
  if (platformName === "darwin") {
    return join(home(), "Library", "Application Support", APP_NAME);
  }
  if (platformName === "win32") {
    const winHome = (): string =>
      typeof env.USERPROFILE === "string" && env.USERPROFILE.trim()
        ? env.USERPROFILE
        : homedir();
    const base =
      typeof env.LOCALAPPDATA === "string" && env.LOCALAPPDATA.trim()
        ? env.LOCALAPPDATA
        : join(winHome(), "AppData", "Local");
    return join(base, APP_NAME);
  }
  const base =
    typeof env.XDG_DATA_HOME === "string" && env.XDG_DATA_HOME.trim()
      ? env.XDG_DATA_HOME
      : join(home(), ".local", "share");
  return join(base, APP_NAME);
}

function secretsDir(dataDir: string): string {
  return join(dataDir, "secrets");
}

export function readBearerToken(dataDir: string): string | null {
  const path = join(secretsDir(dataDir), SECRET_BEARER_TOKEN);
  if (!existsSync(path)) {
    return null;
  }
  const raw = readFileSync(path, "utf-8").trim();
  return raw || null;
}

export function writeBearerToken(dataDir: string, token: string): void {
  mkdirSync(dataDir, { recursive: true });
  mkdirSync(secretsDir(dataDir), { recursive: true });
  const path = join(secretsDir(dataDir), SECRET_BEARER_TOKEN);
  writeFileSync(path, `${token}\n`, "utf-8");
  if (nodePlatform() !== "win32") {
    // Only the secrets dir + token file are single-user permissioned here —
    // the shared data dir itself may hold other, less-sensitive content.
    chmodSync(secretsDir(dataDir), 0o700);
    chmodSync(path, 0o600);
  }
}

export function mintToken(): string {
  return randomBytes(32).toString("hex");
}

/** Load the Config bearer, minting and persisting one if absent (sole authority = Config). */
export function ensureBearerToken(dataDir: string): string {
  const existing = readBearerToken(dataDir);
  if (existing) {
    return existing;
  }
  const minted = mintToken();
  writeBearerToken(dataDir, minted);
  return minted;
}

// --- Health check (ATTACH decision) ---

export type HealthResult = "ok" | "unauthorized" | "unreachable";

export async function checkHealth(
  baseUrl: string,
  token: string,
  fetchImpl: typeof fetch = fetch,
  timeoutMs = 5000,
): Promise<HealthResult> {
  try {
    const response = await fetchImpl(`${baseUrl}/health`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: AbortSignal.timeout(timeoutMs),
    });
    if (response.status === 200) {
      return "ok";
    }
    if (response.status === 401 || response.status === 403) {
      return "unauthorized";
    }
    return "unreachable";
  } catch {
    return "unreachable";
  }
}

// --- Spawn command resolution ---

export interface TeacherCommand {
  command: string;
  args: string[];
  cwd: string;
}

/** `services/teacher` lives 4 levels above the built `out/main` dir; override for tests/dev. */
export function resolveTeacherServiceDir(
  mainDir: string,
  env: NodeJS.ProcessEnv = process.env,
): string {
  const override = env.TEACHER_SERVICE_DIR;
  if (typeof override === "string" && override.trim()) {
    return resolvePath(override.trim());
  }
  return resolvePath(mainDir, "..", "..", "..", "..", "services", "teacher");
}

export function resolveTeacherCommand(
  mainDir: string,
  env: NodeJS.ProcessEnv = process.env,
): TeacherCommand {
  return {
    command: "uv",
    args: ["run", "teacher-api"],
    cwd: resolveTeacherServiceDir(mainDir, env),
  };
}

function sleep(ms: number): Promise<void> {
  return new Promise((res) => setTimeout(res, ms));
}

export interface TeacherHostDeps {
  fetchImpl?: typeof fetch;
  spawnImpl?: typeof nodeSpawn;
  env?: NodeJS.ProcessEnv;
  mainDir?: string;
  onStatus?: (status: TeacherStatus) => void;
  healthTimeoutMs?: number;
  healthPollIntervalMs?: number;
  /** Per-request abort timeout so a single hung fetch cannot block healthTimeoutMs. */
  requestTimeoutMs?: number;
}

/**
 * Thin-host lifecycle: on `start()`, attach to an already-healthy loopback
 * teacher (ATTACH) or spawn a child sharing the same data dir + bearer.
 * A port that answers with the wrong token fails closed — never a silent
 * wrong-token attach.
 */
export class TeacherHost {
  private status: TeacherStatus = {
    state: "stopped",
    base_url: BASE_URL,
    bearer: null,
  };
  private child: ChildProcess | null = null;
  private readonly dataDir: string;
  private readonly fetchImpl: typeof fetch;
  private readonly spawnImpl: typeof nodeSpawn;
  private readonly env: NodeJS.ProcessEnv;
  private readonly mainDir: string;
  private readonly onStatus: (status: TeacherStatus) => void;
  private readonly healthTimeoutMs: number;
  private readonly healthPollIntervalMs: number;
  private readonly requestTimeoutMs: number;
  private startPromise: Promise<TeacherStatus> | null = null;
  /** Bumped by stop() (and each new doStart) so in-flight waitForHealth cannot overwrite stopped. */
  private runId = 0;

  constructor(deps: TeacherHostDeps = {}) {
    this.fetchImpl = deps.fetchImpl ?? fetch;
    this.spawnImpl = deps.spawnImpl ?? nodeSpawn;
    this.env = deps.env ?? process.env;
    this.mainDir = deps.mainDir ?? __dirname;
    this.onStatus = deps.onStatus ?? (() => undefined);
    this.healthTimeoutMs = deps.healthTimeoutMs ?? 8000;
    this.healthPollIntervalMs = deps.healthPollIntervalMs ?? 300;
    this.requestTimeoutMs = deps.requestTimeoutMs ?? 5000;
    this.dataDir = resolveDataDir(this.env);
  }

  getStatus(): TeacherStatus {
    return { ...this.status };
  }

  /** True only when this host is managing a process it spawned (not attached). */
  ownsChildProcess(): boolean {
    return this.child !== null;
  }

  private setStatus(next: Partial<TeacherStatus>): TeacherStatus {
    this.status = { ...this.status, ...next };
    this.onStatus(this.getStatus());
    return this.getStatus();
  }

  /** Re-entry guard: overlapping start()/retry calls share one in-flight attempt. */
  async start(): Promise<TeacherStatus> {
    if (this.startPromise) {
      return this.startPromise;
    }
    this.startPromise = this.doStart().finally(() => {
      this.startPromise = null;
    });
    return this.startPromise;
  }

  private async doStart(): Promise<TeacherStatus> {
    const runId = ++this.runId;

    let token: string;
    try {
      token = ensureBearerToken(this.dataDir);
    } catch (err) {
      return this.setStatusIfCurrent(runId, {
        state: "error",
        message: `Не удалось подготовить токен доступа: ${String(err)}`,
      });
    }
    if (runId !== this.runId) {
      return this.getStatus();
    }
    this.setStatus({ bearer: token });

    // Already running + healthy: keep the owned/attached process (ATTACH / no tear-down).
    if (this.status.state === "running") {
      const stillOk = await checkHealth(
        this.status.base_url,
        token,
        this.fetchImpl,
        this.requestTimeoutMs,
      );
      if (runId !== this.runId) {
        return this.getStatus();
      }
      if (stillOk === "ok") {
        return this.getStatus();
      }
    }

    // Restart path only: drop a leftover owned child, then attach or spawn.
    this.killOwnedChild();
    if (runId !== this.runId) {
      return this.getStatus();
    }
    this.setStatus({ state: "starting", message: undefined });

    const attach = await checkHealth(
      this.status.base_url,
      token,
      this.fetchImpl,
      this.requestTimeoutMs,
    );
    if (runId !== this.runId) {
      return this.getStatus();
    }
    if (attach === "ok") {
      return this.setStatus({ state: "running", message: undefined });
    }
    if (attach === "unauthorized") {
      // Something else is listening on the port with a different token — fail closed.
      return this.setStatus({
        state: "error",
        message: "Порт учителя занят другим процессом с иным токеном доступа",
      });
    }

    try {
      this.spawnChild(token);
    } catch (err) {
      return this.setStatusIfCurrent(runId, {
        state: "error",
        message: String(err),
      });
    }

    const ready = await this.waitForHealth(token, runId);
    if (runId !== this.runId) {
      return this.getStatus();
    }
    if (ready) {
      return this.setStatus({ state: "running", message: undefined });
    }
    // Never leave a spawned-but-unhealthy child running behind an error status.
    this.killOwnedChild();
    return this.setStatusIfCurrent(runId, {
      state: "error",
      message: "Учитель не запустился — проверьте установку сервиса",
    });
  }

  private setStatusIfCurrent(
    runId: number,
    next: Partial<TeacherStatus>,
  ): TeacherStatus {
    if (runId !== this.runId) {
      return this.getStatus();
    }
    return this.setStatus(next);
  }

  private spawnChild(token: string): void {
    const { command, args, cwd } = resolveTeacherCommand(
      this.mainDir,
      this.env,
    );
    const child = this.spawnImpl(command, args, {
      cwd,
      env: {
        ...this.env,
        TEACHER_AUTH_TOKEN: token,
        TEACHER_DATA_DIR: this.dataDir,
      },
      stdio: "ignore",
    });
    child.on("exit", () => {
      if (this.child === child) {
        this.child = null;
        if (this.status.state === "running") {
          this.setStatus({ state: "stopped" });
        }
      }
    });
    // Without an 'error' listener, a spawn failure (e.g. ENOENT) would throw an
    // unhandled error on this EventEmitter and crash the Electron main process.
    child.on("error", (err) => {
      if (this.child === child) {
        this.child = null;
        // Abort in-flight waitForHealth so doStart does not overwrite this error.
        this.runId += 1;
        this.setStatus({
          state: "error",
          message: `Не удалось запустить учителя: ${String(err)}`,
        });
      }
    });
    this.child = child;
  }

  private async waitForHealth(token: string, runId: number): Promise<boolean> {
    const deadline = Date.now() + this.healthTimeoutMs;
    do {
      if (runId !== this.runId) {
        return false;
      }
      const result = await checkHealth(
        this.status.base_url,
        token,
        this.fetchImpl,
        this.requestTimeoutMs,
      );
      if (result === "ok") {
        return true;
      }
      if (result === "unauthorized") {
        return false;
      }
      await sleep(this.healthPollIntervalMs);
    } while (Date.now() < deadline);
    return false;
  }

  private killOwnedChild(): void {
    if (this.child) {
      this.child.kill();
      this.child = null;
    }
  }

  /** Stop only the process this host spawned; an attached external process is left running. */
  stop(): void {
    // Invalidate any in-flight doStart/waitForHealth so it cannot flip status back to running.
    this.runId += 1;
    this.killOwnedChild();
    this.setStatus({ state: "stopped" });
  }
}

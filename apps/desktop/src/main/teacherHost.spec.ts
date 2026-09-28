import { EventEmitter } from "node:events";
import {
  existsSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  statSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  BASE_URL,
  checkHealth,
  ensureBearerToken,
  readBearerToken,
  resolveDataDir,
  resolveTeacherCommand,
  resolveTeacherServiceDir,
  TeacherHost,
  writeBearerToken,
} from "./teacherHost";

function jsonResponse(status: number): Response {
  return new Response(JSON.stringify({ status: "ok" }), { status });
}

describe("resolveDataDir", () => {
  it("prefers a non-empty TEACHER_DATA_DIR override on every platform", () => {
    const env = { TEACHER_DATA_DIR: "/tmp/override-data" };
    expect(resolveDataDir(env, "linux")).toBe("/tmp/override-data");
    expect(resolveDataDir(env, "darwin")).toBe("/tmp/override-data");
    expect(resolveDataDir(env, "win32")).toBe("/tmp/override-data");
  });

  it("treats whitespace-only override as unset", () => {
    const env = { TEACHER_DATA_DIR: "   ", HOME: "/home/dev" };
    expect(resolveDataDir(env, "linux")).not.toBe("   ");
  });

  it("falls back to XDG_DATA_HOME / ~/.local/share on linux", () => {
    expect(resolveDataDir({ XDG_DATA_HOME: "/xdg" }, "linux")).toBe(
      join("/xdg", "ai-language-teacher"),
    );
    expect(resolveDataDir({ HOME: "/home/dev" }, "linux")).toBe(
      join("/home/dev", ".local", "share", "ai-language-teacher"),
    );
  });

  it("falls back to macOS Application Support", () => {
    expect(resolveDataDir({ HOME: "/Users/dev" }, "darwin")).toBe(
      join(
        "/Users/dev",
        "Library",
        "Application Support",
        "ai-language-teacher",
      ),
    );
  });

  it("falls back to Windows LOCALAPPDATA", () => {
    expect(
      resolveDataDir({ LOCALAPPDATA: "C:/Users/dev/AppData/Local" }, "win32"),
    ).toBe(join("C:/Users/dev/AppData/Local", "ai-language-teacher"));
  });
});

describe("bearer token mint/read (Config secrets layout)", () => {
  let dir: string;

  beforeEach(() => {
    dir = mkdtempSync(join(tmpdir(), "teacher-host-test-"));
  });

  afterEach(() => {
    rmSync(dir, { recursive: true, force: true });
  });

  it("mints and persists a token when none exists, then reuses it", () => {
    expect(readBearerToken(dir)).toBeNull();
    const minted = ensureBearerToken(dir);
    expect(minted).toHaveLength(64); // 32 random bytes as hex
    expect(readBearerToken(dir)).toBe(minted);

    const reused = ensureBearerToken(dir);
    expect(reused).toBe(minted);
  });

  it("writes the secret file with single-user permissions", () => {
    writeBearerToken(dir, "abc123");
    const path = join(dir, "secrets", "bearer_token");
    expect(existsSync(path)).toBe(true);
    expect(readFileSync(path, "utf-8").trim()).toBe("abc123");
    if (process.platform !== "win32") {
      expect(statSync(path).mode & 0o777).toBe(0o600);
      expect(statSync(join(dir, "secrets")).mode & 0o777).toBe(0o700);
    }
  });

  it("remint after clearing app-data invalidates the prior token", () => {
    const first = ensureBearerToken(dir);
    rmSync(dir, { recursive: true, force: true });
    const second = ensureBearerToken(dir);
    expect(second).not.toBe(first);
  });
});

describe("checkHealth", () => {
  it("returns ok for 200 and sends Authorization Bearer", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(200));
    expect(await checkHealth(BASE_URL, "tok", fetchImpl)).toBe("ok");
    expect(fetchImpl).toHaveBeenCalledWith(
      `${BASE_URL}/health`,
      expect.objectContaining({
        headers: { Authorization: "Bearer tok" },
      }),
    );
  });

  it("returns unauthorized for 401/403 (fail closed on token mismatch)", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(401));
    expect(await checkHealth(BASE_URL, "tok", fetchImpl)).toBe("unauthorized");
    expect(fetchImpl).toHaveBeenCalledWith(
      `${BASE_URL}/health`,
      expect.objectContaining({
        headers: { Authorization: "Bearer tok" },
      }),
    );
    fetchImpl.mockResolvedValue(jsonResponse(403));
    expect(await checkHealth(BASE_URL, "tok", fetchImpl)).toBe("unauthorized");
  });

  it("returns unreachable on network error or other statuses", async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new Error("ECONNREFUSED"));
    expect(await checkHealth(BASE_URL, "tok", fetchImpl)).toBe("unreachable");
    fetchImpl.mockResolvedValue(jsonResponse(500));
    expect(await checkHealth(BASE_URL, "tok", fetchImpl)).toBe("unreachable");
  });
});

describe("resolveTeacherCommand", () => {
  it("resolves services/teacher four levels above the built main dir by default", () => {
    const mainDir = "/repo/apps/desktop/out/main";
    const cmd = resolveTeacherCommand(mainDir, {});
    expect(cmd.command).toBe("uv");
    expect(cmd.args).toEqual(["run", "teacher-api"]);
    expect(cmd.cwd).toBe("/repo/services/teacher");
  });

  it("honors TEACHER_SERVICE_DIR override", () => {
    const cwd = resolveTeacherServiceDir("/repo/apps/desktop/out/main", {
      TEACHER_SERVICE_DIR: "/custom/teacher",
    });
    expect(cwd).toBe("/custom/teacher");
  });
});

describe("TeacherHost", () => {
  let dir: string;

  beforeEach(() => {
    dir = mkdtempSync(join(tmpdir(), "teacher-host-lifecycle-"));
  });

  afterEach(() => {
    rmSync(dir, { recursive: true, force: true });
  });

  it("attaches without spawning when loopback already answers with the Config bearer", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(200));
    const spawnImpl = vi.fn();
    const statuses: string[] = [];
    const host = new TeacherHost({
      fetchImpl,
      spawnImpl: spawnImpl as never,
      env: { TEACHER_DATA_DIR: dir },
      onStatus: (s) => statuses.push(s.state),
    });

    const result = await host.start();
    expect(result.state).toBe("running");
    expect(spawnImpl).not.toHaveBeenCalled();
    expect(host.ownsChildProcess()).toBe(false);
    expect(statuses).toEqual(["stopped", "starting", "running"]);
    // AUTH_BRIDGE: attach must report the same Config bearer + fixed base_url.
    expect(result.bearer).toBe(readBearerToken(dir));
    expect(result.base_url).toBe(BASE_URL);
  });

  it("re-entrant start() while already healthy does not kill an owned child", async () => {
    let callCount = 0;
    const fetchImpl = vi.fn().mockImplementation(async () => {
      callCount += 1;
      return callCount < 3
        ? Promise.reject(new Error("ECONNREFUSED"))
        : jsonResponse(200);
    });
    const fakeChild = new EventEmitter() as EventEmitter & { kill: () => void };
    fakeChild.kill = vi.fn();
    const spawnImpl = vi.fn().mockReturnValue(fakeChild);

    const host = new TeacherHost({
      fetchImpl,
      spawnImpl: spawnImpl as never,
      env: { TEACHER_DATA_DIR: dir },
      healthPollIntervalMs: 1,
    });

    await host.start();
    expect(host.ownsChildProcess()).toBe(true);
    expect(fakeChild.kill).not.toHaveBeenCalled();

    const again = await host.start();
    expect(again.state).toBe("running");
    expect(spawnImpl).toHaveBeenCalledTimes(1);
    expect(fakeChild.kill).not.toHaveBeenCalled();
    expect(host.ownsChildProcess()).toBe(true);
  });

  it("overlapping start() calls share one in-flight attempt", async () => {
    let release!: (value: Response) => void;
    const firstHealth = new Promise<Response>((resolve) => {
      release = resolve;
    });
    let fetchCalls = 0;
    const fetchImpl = vi.fn().mockImplementation(async () => {
      fetchCalls += 1;
      if (fetchCalls === 1) {
        return firstHealth;
      }
      return jsonResponse(200);
    });
    const spawnImpl = vi.fn();
    const host = new TeacherHost({
      fetchImpl,
      spawnImpl: spawnImpl as never,
      env: { TEACHER_DATA_DIR: dir },
    });

    const a = host.start();
    const b = host.start();
    release(jsonResponse(200));
    const [ra, rb] = await Promise.all([a, b]);
    expect(ra.state).toBe("running");
    expect(rb.state).toBe("running");
    expect(spawnImpl).not.toHaveBeenCalled();
    // One attach probe for the shared attempt (bearer set, then health).
    expect(fetchCalls).toBe(1);
  });

  it("fails closed (no spawn) when the port answers with a mismatched token", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(401));
    const spawnImpl = vi.fn();
    const host = new TeacherHost({
      fetchImpl,
      spawnImpl: spawnImpl as never,
      env: { TEACHER_DATA_DIR: dir },
    });

    const result = await host.start();
    expect(result.state).toBe("error");
    expect(spawnImpl).not.toHaveBeenCalled();
    expect(host.ownsChildProcess()).toBe(false);
  });

  it("spawns a child sharing the data dir + bearer when nothing is listening, then reports running", async () => {
    let callCount = 0;
    const fetchImpl = vi.fn().mockImplementation(async () => {
      callCount += 1;
      return callCount < 3
        ? Promise.reject(new Error("ECONNREFUSED"))
        : jsonResponse(200);
    });
    const fakeChild = new EventEmitter() as EventEmitter & { kill: () => void };
    fakeChild.kill = vi.fn();
    const spawnImpl = vi.fn().mockReturnValue(fakeChild);

    const host = new TeacherHost({
      fetchImpl,
      spawnImpl: spawnImpl as never,
      env: { TEACHER_DATA_DIR: dir },
      healthPollIntervalMs: 1,
    });

    const result = await host.start();
    expect(result.state).toBe("running");
    expect(spawnImpl).toHaveBeenCalledTimes(1);
    const [command, args, options] = spawnImpl.mock.calls[0] as [
      string,
      string[],
      { env: Record<string, string | undefined> },
    ];
    expect(command).toBe("uv");
    expect(args).toEqual(["run", "teacher-api"]);
    expect(options.env.TEACHER_DATA_DIR).toBe(dir);
    expect(typeof options.env.TEACHER_AUTH_TOKEN).toBe("string");
    expect(options.env.TEACHER_AUTH_TOKEN).toBe(result.bearer);
    expect(host.ownsChildProcess()).toBe(true);
    // AUTH_BRIDGE: spawn must report the same Config bearer + fixed base_url.
    expect(result.bearer).toBe(readBearerToken(dir));
    expect(result.base_url).toBe(BASE_URL);

    host.stop();
    expect(fakeChild.kill).toHaveBeenCalledTimes(1);
    expect(host.ownsChildProcess()).toBe(false);
    expect(host.getStatus().state).toBe("stopped");
  });

  it("reports stopped and releases ownership when a spawned child exits on its own", async () => {
    let callCount = 0;
    const fetchImpl = vi.fn().mockImplementation(async () => {
      callCount += 1;
      return callCount < 2
        ? Promise.reject(new Error("ECONNREFUSED"))
        : jsonResponse(200);
    });
    const fakeChild = new EventEmitter() as EventEmitter & { kill: () => void };
    fakeChild.kill = vi.fn();
    const spawnImpl = vi.fn().mockReturnValue(fakeChild);

    const host = new TeacherHost({
      fetchImpl,
      spawnImpl: spawnImpl as never,
      env: { TEACHER_DATA_DIR: dir },
      healthPollIntervalMs: 1,
    });

    const result = await host.start();
    expect(result.state).toBe("running");
    expect(host.ownsChildProcess()).toBe(true);

    fakeChild.emit("exit", 0, null);

    expect(host.ownsChildProcess()).toBe(false);
    expect(host.getStatus().state).toBe("stopped");
  });

  it("reports error when a spawned child never becomes healthy within the timeout", async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new Error("ECONNREFUSED"));
    const fakeChild = new EventEmitter() as EventEmitter & { kill: () => void };
    fakeChild.kill = vi.fn();
    const spawnImpl = vi.fn().mockReturnValue(fakeChild);

    const host = new TeacherHost({
      fetchImpl,
      spawnImpl: spawnImpl as never,
      env: { TEACHER_DATA_DIR: dir },
      healthTimeoutMs: 5,
      healthPollIntervalMs: 1,
    });

    const result = await host.start();
    expect(result.state).toBe("error");
    expect(fakeChild.kill).toHaveBeenCalledTimes(1);
    expect(host.ownsChildProcess()).toBe(false);
  });

  it("reports error and clears ownership when a spawned child emits error", async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new Error("ECONNREFUSED"));
    const fakeChild = new EventEmitter() as EventEmitter & { kill: () => void };
    fakeChild.kill = vi.fn();
    const spawnImpl = vi.fn().mockReturnValue(fakeChild);

    const host = new TeacherHost({
      fetchImpl,
      spawnImpl: spawnImpl as never,
      env: { TEACHER_DATA_DIR: dir },
      healthTimeoutMs: 50,
      healthPollIntervalMs: 5,
    });

    const pending = host.start();
    // Allow spawn to register, then fail the child before health succeeds.
    await new Promise((r) => setTimeout(r, 2));
    fakeChild.emit("error", new Error("ENOENT"));
    const result = await pending;
    expect(result.state).toBe("error");
    expect(result.message).toMatch(/Не удалось запустить учителя/);
    expect(host.ownsChildProcess()).toBe(false);
  });

  it("stop() during waitForHealth leaves status stopped (not flipped back to running)", async () => {
    let callCount = 0;
    const fetchImpl = vi.fn().mockImplementation(async () => {
      callCount += 1;
      if (callCount === 1) {
        return Promise.reject(new Error("ECONNREFUSED"));
      }
      await new Promise((r) => setTimeout(r, 30));
      return jsonResponse(200);
    });
    const fakeChild = new EventEmitter() as EventEmitter & { kill: () => void };
    fakeChild.kill = vi.fn();
    const spawnImpl = vi.fn().mockReturnValue(fakeChild);

    const host = new TeacherHost({
      fetchImpl,
      spawnImpl: spawnImpl as never,
      env: { TEACHER_DATA_DIR: dir },
      healthTimeoutMs: 200,
      healthPollIntervalMs: 5,
    });

    const pending = host.start();
    await new Promise((r) => setTimeout(r, 5));
    host.stop();
    const result = await pending;
    expect(result.state).toBe("stopped");
    expect(host.getStatus().state).toBe("stopped");
  });

  it("stop() on an attached (not spawned) process only marks stopped locally", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(200));
    const host = new TeacherHost({
      fetchImpl,
      spawnImpl: vi.fn() as never,
      env: { TEACHER_DATA_DIR: dir },
    });
    await host.start();
    expect(host.ownsChildProcess()).toBe(false);
    host.stop();
    expect(host.getStatus().state).toBe("stopped");
  });
});

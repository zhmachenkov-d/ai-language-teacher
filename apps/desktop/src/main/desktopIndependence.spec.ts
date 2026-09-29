/**
 * Closes the 1.1 verification gap: `npm run build` alone would stay green if
 * main/preload gained a hard live-teacher dependency at module load. Prove via
 * static coupling scan + constructor smoke that the host remains startable
 * without an already-listening teacher on :8765.
 */
import { describe, expect, it, vi } from "vitest";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { TeacherHost } from "./teacherHost";

const mainSrc = readFileSync(join(__dirname, "index.ts"), "utf8");
const preloadSrc = readFileSync(join(__dirname, "../preload/index.ts"), "utf8");

/** Strip line and block comments so order scans ignore commented-out calls. */
function stripComments(source: string): string {
  return source
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/(^|[^:])\/\/.*$/gm, "$1");
}

describe("desktop main/preload without a live teacher", () => {
  it("main constructs TeacherHost at load but does not eagerly start it", () => {
    const body = stripComments(mainSrc);
    expect(body).toMatch(/new\s+TeacherHost\s*\(/);

    // Eager module-level start: unindented statement (whenReady / handle
    // callbacks are indented and may call start later).
    expect(body).not.toMatch(/^(?:await\s+)?teacherHost\.start\s*\(/m);
  });

  it("whenReady shows the window before awaiting teacherHost.start", () => {
    const body = stripComments(mainSrc);
    const whenReadyIdx = body.search(/app\.whenReady\s*\(\s*\)\s*\.then\s*\(/);
    expect(whenReadyIdx).toBeGreaterThanOrEqual(0);
    const afterReady = body.slice(whenReadyIdx);
    const showIdx = afterReady.search(/\bshowMainWindow\s*\(/);
    const startIdx = afterReady.search(/await\s+teacherHost\.start\s*\(/);
    expect(showIdx).toBeGreaterThanOrEqual(0);
    expect(startIdx).toBeGreaterThan(showIdx);
  });

  it("main/preload have no direct HTTP probe of the teacher loopback", () => {
    const mainBody = stripComments(mainSrc);
    const preloadBody = stripComments(preloadSrc);

    // Domain HTTP stays in TeacherHost / renderer fetch — not in entry wiring.
    expect(preloadBody).not.toMatch(/\bfetch\s*\(/);
    expect(preloadBody).not.toMatch(/\bhttp\.(get|request)\s*\(/);
    expect(preloadBody).not.toMatch(/127\.0\.0\.1:8765|localhost:8765/);

    expect(mainBody).not.toMatch(/\bfetch\s*\(/);
    expect(mainBody).not.toMatch(/\bhttp\.(get|request)\s*\(/);
    expect(mainBody).not.toMatch(/127\.0\.0\.1:8765|localhost:8765/);
  });

  it("TeacherHost construction does not touch the network until start()", () => {
    const dir = mkdtempSync(join(tmpdir(), "desktop-independence-"));
    const fetchImpl = vi.fn();
    const spawnImpl = vi.fn();
    try {
      const host = new TeacherHost({
        env: { TEACHER_DATA_DIR: dir },
        fetchImpl: fetchImpl as never,
        spawnImpl: spawnImpl as never,
      });
      expect(host.getStatus().state).toBe("stopped");
      expect(fetchImpl).not.toHaveBeenCalled();
      expect(spawnImpl).not.toHaveBeenCalled();
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });
});

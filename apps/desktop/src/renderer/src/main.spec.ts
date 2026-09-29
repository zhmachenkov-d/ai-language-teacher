/**
 * Closes the 1.5 verification gap: App.spec injects its own router, so removing
 * `.use(createAppRouter())` from production main.ts would leave the suite green.
 */
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("production main.ts entry wiring", () => {
  it("installs createAppRouter on the Vue app before mount", () => {
    const mainSrc = readFileSync(resolve(__dirname, "main.ts"), "utf8");
    expect(mainSrc).toMatch(
      /import\s*\{\s*createAppRouter\s*\}\s*from\s*['"]\.\/router['"]/,
    );
    expect(mainSrc).toMatch(
      /createApp\s*\(\s*App\s*\)\s*\.use\s*\(\s*createAppRouter\s*\(\s*\)\s*\)\s*\.mount\s*\(/,
    );
  });
});

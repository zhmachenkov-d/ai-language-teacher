import { describe, expect, it } from "vitest";
import { gateDestination, isGatedRoute, isOnboardingRoute } from "./gate";

describe("onboarding gate", () => {
  it("routes incomplete intake to wizard", () => {
    expect(
      gateDestination({ intake_step: "goals", consent_complete: false }),
    ).toBe("onboarding");
  });

  it("routes intake complete without consent to consent", () => {
    expect(
      gateDestination({ intake_step: "complete", consent_complete: false }),
    ).toBe("onboarding-consent");
  });

  it("routes consent_complete to placement stub (not calendar)", () => {
    expect(
      gateDestination({ intake_step: "complete", consent_complete: true }),
    ).toBe("onboarding-placement");
  });

  it("marks calendar and home as gated", () => {
    expect(isGatedRoute("calendar")).toBe(true);
    expect(isGatedRoute("home-redirect")).toBe(true);
    expect(isGatedRoute("settings")).toBe(false);
  });

  it("recognizes onboarding routes including placement", () => {
    expect(isOnboardingRoute("onboarding")).toBe(true);
    expect(isOnboardingRoute("onboarding-consent")).toBe(true);
    expect(isOnboardingRoute("onboarding-placement")).toBe(true);
    expect(isOnboardingRoute("calendar")).toBe(false);
  });
});

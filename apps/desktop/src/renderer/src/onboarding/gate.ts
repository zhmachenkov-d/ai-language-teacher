/**
 * First-run GATE: unfinished intake → wizard; intake done && !consent → consent;
 * consent_complete → placement stub (calendar climax is Story 2.6 — never treat
 * intake/consent alone as onboarded).
 */

import type { LearnerProfile } from "../services/teacherClient";

export type GateDestination =
  | "onboarding"
  | "onboarding-consent"
  | "onboarding-placement"
  | "calendar";

export function gateDestination(
  learner: Pick<LearnerProfile, "intake_step" | "consent_complete">,
): GateDestination {
  if (learner.intake_step !== "complete") {
    return "onboarding";
  }
  if (!learner.consent_complete) {
    return "onboarding-consent";
  }
  // Placement + climax not done in 2.2 — keep calendar gated.
  return "onboarding-placement";
}

export function isGatedRoute(routeName: string | symbol | null | undefined): boolean {
  return routeName === "calendar" || routeName === "home-redirect";
}

/** Routes that participate in onboarding RESUME / handoff (not Settings). */
export function isOnboardingRoute(
  routeName: string | symbol | null | undefined,
): boolean {
  return (
    routeName === "onboarding" ||
    routeName === "onboarding-consent" ||
    routeName === "onboarding-placement"
  );
}

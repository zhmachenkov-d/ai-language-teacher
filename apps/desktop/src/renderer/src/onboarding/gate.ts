/**
 * First-run GATE: unfinished intake → wizard; intake done && !consent → consent;
 * consent_complete && !placement_complete → placement; placement_complete →
 * plan stub (calendar climax is Story 2.6 — never treat intake/consent/placement
 * alone as onboarded).
 */

import type { LearnerProfile } from "../services/teacherClient";

export type GateDestination =
  | "onboarding"
  | "onboarding-consent"
  | "onboarding-placement"
  | "onboarding-plan"
  | "calendar";

export function gateDestination(
  learner: Pick<
    LearnerProfile,
    "intake_step" | "consent_complete" | "placement_complete"
  >,
): GateDestination {
  if (learner.intake_step !== "complete") {
    return "onboarding";
  }
  if (!learner.consent_complete) {
    return "onboarding-consent";
  }
  if (!learner.placement_complete) {
    return "onboarding-placement";
  }
  // Living plan creation/animation (2.4) + calendar climax (2.6) not done yet —
  // hand off to the plan chrome stub, never calendar-as-onboarded.
  return "onboarding-plan";
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
    routeName === "onboarding-placement" ||
    routeName === "onboarding-plan"
  );
}

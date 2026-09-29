/**
 * First-run GATE: unfinished intake → wizard; intake done && !consent → consent;
 * consent_complete && !placement_complete → placement; placement_complete →
 * plan stub (calendar climax is Story 2.6 — never treat intake/consent/placement
 * or plan_complete alone as onboarded).
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
    "intake_step" | "consent_complete" | "placement_complete" | "plan_complete"
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
  // Living plan FLAG may be set (2.4) but calendar climax stays 2.6 —
  // `plan_complete` alone must never open calendar.
  void learner.plan_complete;
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

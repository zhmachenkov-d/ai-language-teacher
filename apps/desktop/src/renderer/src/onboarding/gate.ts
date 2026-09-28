/**
 * First-run GATE: unfinished intake → wizard; intake done → consent stub
 * (calendar climax is Story 2.6 — never treat intake alone as onboarded).
 */

import type { LearnerProfile } from "../services/teacherClient";

export type GateDestination = "onboarding" | "onboarding-consent" | "calendar";

export function gateDestination(learner: Pick<LearnerProfile, "intake_step">): GateDestination {
  if (learner.intake_step !== "complete") {
    return "onboarding";
  }
  // Consent + climax not done in 2.1 — keep calendar gated.
  return "onboarding-consent";
}

export function isGatedRoute(routeName: string | symbol | null | undefined): boolean {
  return routeName === "calendar" || routeName === "home-redirect";
}

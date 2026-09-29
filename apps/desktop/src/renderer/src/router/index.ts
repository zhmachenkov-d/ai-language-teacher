import {
  createRouter,
  createWebHashHistory,
  type RouteLocationNormalized,
  type Router,
} from 'vue-router'
import CalendarHome from '../views/CalendarHome.vue'
import SettingsView from '../views/SettingsView.vue'
import TitleStubView from '../views/TitleStubView.vue'
import OnboardingWizard from '../views/OnboardingWizard.vue'
import OnboardingConsent from '../views/OnboardingConsent.vue'
import OnboardingPlacement from '../views/OnboardingPlacement.vue'
import OnboardingPlanStub from '../views/OnboardingPlanStub.vue'
import {
  gateDestination,
  isGatedRoute,
  isOnboardingRoute,
} from '../onboarding/gate'
import {
  fetchLearner,
  getTeacherAuth,
  type LearnerProfile,
} from '../services/teacherClient'

/** Optional override for Vitest — when set, GATE uses this learner instead of HTTP. */
let gateLearnerOverride: LearnerProfile | null | undefined

export function setGateLearnerOverride(
  learner: LearnerProfile | null | undefined,
): void {
  gateLearnerOverride = learner
}

async function resolveLearnerForGate(): Promise<LearnerProfile | null> {
  if (gateLearnerOverride !== undefined) {
    return gateLearnerOverride
  }
  try {
    const auth = await getTeacherAuth()
    if (auth.state !== 'running' || !auth.bearer) {
      return null
    }
    return await fetchLearner(auth)
  } catch {
    return null
  }
}

export function createAppRouter(): Router {
  const router = createRouter({
    history: createWebHashHistory(),
    routes: [
      {
        path: '/',
        name: 'home-redirect',
        redirect: { name: 'calendar' },
      },
      {
        path: '/onboarding',
        name: 'onboarding',
        component: OnboardingWizard,
        meta: { hideNav: true },
      },
      {
        path: '/onboarding/consent',
        name: 'onboarding-consent',
        component: OnboardingConsent,
        meta: { hideNav: true },
      },
      {
        path: '/onboarding/placement',
        name: 'onboarding-placement',
        component: OnboardingPlacement,
        meta: { hideNav: true },
      },
      {
        path: '/onboarding/plan',
        name: 'onboarding-plan',
        component: OnboardingPlanStub,
        meta: { hideNav: true },
      },
      {
        path: '/calendar',
        name: 'calendar',
        component: CalendarHome,
      },
      {
        path: '/plan',
        name: 'plan',
        component: TitleStubView,
        props: { title: 'План' },
      },
      {
        path: '/progress',
        name: 'progress',
        component: TitleStubView,
        props: { title: 'Прогресс' },
      },
      {
        path: '/settings',
        name: 'settings',
        component: SettingsView,
      },
      {
        path: '/:pathMatch(.*)*',
        redirect: '/calendar',
      },
    ],
  })

  router.beforeEach(async (to: RouteLocationNormalized) => {
    if (isOnboardingRoute(to.name)) {
      // Still apply RESUME / post-intake handoff when hitting the wrong onboarding route.
      const learner = await resolveLearnerForGate()
      if (learner == null) {
        // Fail closed: never linger on consent/placement without a learner projection.
        return to.name === 'onboarding' ? true : { name: 'onboarding' }
      }
      const dest = gateDestination(learner)
      if (to.name !== dest) {
        return { name: dest }
      }
      return true
    }

    if (!isGatedRoute(to.name)) {
      return true
    }

    const learner = await resolveLearnerForGate()
    if (learner == null) {
      // Teacher down / auth missing — fail toward wizard (no calendar-as-done).
      return { name: 'onboarding' }
    }
    const dest = gateDestination(learner)
    if (dest === 'calendar') {
      return true
    }
    return { name: dest }
  })

  return router
}

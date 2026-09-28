import { createRouter, createWebHashHistory, type Router } from 'vue-router'
import CalendarHome from '../views/CalendarHome.vue'
import SettingsView from '../views/SettingsView.vue'
import TitleStubView from '../views/TitleStubView.vue'

export function createAppRouter(): Router {
  return createRouter({
    history: createWebHashHistory(),
    routes: [
      {
        path: '/',
        redirect: { name: 'calendar' }
      },
      {
        path: '/calendar',
        name: 'calendar',
        component: CalendarHome
      },
      {
        path: '/plan',
        name: 'plan',
        component: TitleStubView,
        props: { title: 'План' }
      },
      {
        path: '/progress',
        name: 'progress',
        component: TitleStubView,
        props: { title: 'Прогресс' }
      },
      {
        path: '/settings',
        name: 'settings',
        component: SettingsView
      },
      {
        path: '/:pathMatch(.*)*',
        redirect: { name: 'calendar' }
      }
    ]
  })
}

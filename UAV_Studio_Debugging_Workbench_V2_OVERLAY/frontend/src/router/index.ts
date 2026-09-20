import { createRouter, createWebHistory } from 'vue-router'
import AircraftLibrary from '../views/AircraftLibrary.vue'
import Assembly from '../views/Assembly.vue'
import Debugging from '../views/Debugging.vue'
import FlightLab from '../views/FlightLab.vue'
import History from '../views/History.vue'
import Replay from '../views/Replay.vue'
import ComponentLibrary from '../views/ComponentLibrary.vue'
import Settings from '../views/Settings.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import { useAuthStore } from '../stores/auth'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: Login, meta: { public: true } },
    { path: '/register', component: Register, meta: { public: true } },
    { path: '/', redirect: '/aircraft' },
    { path: '/aircraft', component: AircraftLibrary },
    { path: '/assembly', component: Assembly },
    { path: '/debugging', component: Debugging },
    { path: '/flight', component: FlightLab },
    { path: '/history', component: History },
    { path: '/history/:id', component: Replay },
    { path: '/components', component: ComponentLibrary },
    { path: '/settings', component: Settings },
  ],
})

router.beforeEach(async to => {
  const auth = useAuthStore()
  await auth.initialize()

  if (to.meta.public) {
    if (auth.authenticated) return '/aircraft'
    return true
  }

  if (!auth.authenticated) {
    return {
      path: '/login',
      query: to.fullPath !== '/' ? { redirect: to.fullPath } : undefined,
    }
  }
  return true
})

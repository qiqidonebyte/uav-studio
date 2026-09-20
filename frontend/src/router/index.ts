import { createRouter, createWebHistory } from 'vue-router'
import AircraftLibrary from '../views/AircraftLibrary.vue'
import Assembly from '../views/Assembly.vue'
import FlightLab from '../views/FlightLab.vue'
import History from '../views/History.vue'
import Replay from '../views/Replay.vue'
import ComponentLibrary from '../views/ComponentLibrary.vue'
import Settings from '../views/Settings.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/aircraft' },
    { path: '/aircraft', component: AircraftLibrary },
    { path: '/assembly', component: Assembly },
    { path: '/flight', component: FlightLab },
    { path: '/history', component: History },
    { path: '/history/:id', component: Replay },
    { path: '/components', component: ComponentLibrary },
    { path: '/settings', component: Settings },
  ],
})

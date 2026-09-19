import { createRouter, createWebHistory } from 'vue-router'
import Assembly from '../views/Assembly.vue'
import FlightLab from '../views/FlightLab.vue'
import History from '../views/History.vue'
import Replay from '../views/Replay.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/assembly' },
    { path: '/assembly', component: Assembly },
    { path: '/flight', component: FlightLab },
    { path: '/history', component: History },
    { path: '/history/:id', component: Replay }
  ]
})

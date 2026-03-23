import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useUserStore } from '../store/user'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('../components/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('../views/Home.vue')
      },
      {
        path: 'planning',
        name: 'Planning',
        component: () => import('../views/BossPlanning.vue'),
        meta: { roles: ['Boss', 'Admin', 'Sales'] }
      },
      {
        path: 'inventory',
        name: 'Inventory',
        component: () => import('../views/InventoryQuery.vue')
      },
      {
        path: 'inbound',
        name: 'Inbound',
        component: () => import('../views/Inbound.vue'),
        meta: { roles: ['Prod', 'Admin', 'Sales'] }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth && !userStore.isAuthenticated) {
    next({ name: 'Login' })
  } else if (to.name === 'Login' && userStore.isAuthenticated) {
    next({ name: 'Home' })
  } else {
    // Role based access control could be added here
    next()
  }
})

export default router

// frontend/src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/services',
    name: 'Services',
    component: () => import('../views/Services.vue')
  },
  {
    path: '/mcp',
    name: 'Mcp',
    redirect: '/mcp/combination', // Redirect to the first sub-menu item
    component: () => import('../views/McpManagement.vue'), // A parent component might be needed, or a generic layout
    children: [
      {
        path: 'combination',
        name: 'McpCombination',
        component: () => import('../views/McpCombination.vue')
      },
      {
        path: 'management',
        name: 'McpManagement',
        component: () => import('../views/McpManagement.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

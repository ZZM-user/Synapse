// frontend/src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated } from '../utils/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/services',
    name: 'Services',
    component: () => import('../views/Services.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/mcp/combination',
    name: 'McpCombination',
    component: () => import('../views/McpCombination.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/mcp/management',
    name: 'McpManagement',
    component: () => import('../views/McpManagement.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫：检查认证状态
router.beforeEach((to, from, next) => {
  const requiresAuth = to.meta.requiresAuth !== false;

  if (requiresAuth && !isAuthenticated()) {
    // 需要认证但未登录，跳转到登录页
    next({
      path: '/login',
      query: { redirect: to.fullPath }
    });
  } else if (to.path === '/login' && isAuthenticated()) {
    // 已登录用户访问登录页，跳转到首页
    next({ path: '/' });
  } else {
    next();
  }
});

export default router

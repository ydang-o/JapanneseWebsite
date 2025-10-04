import { createRouter, createWebHashHistory } from 'vue-router'
import Home from '../pages/Home.vue'
import Login from '../pages/Login.vue'
import Register from '../pages/Register.vue'
import User from '../pages/User.vue'
import Admin from '../pages/Admin.vue'

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', component: Home, alias: ['/home'] },
    { path: '/login', component: Login },
    { path: '/register', component: Register },
    { path: '/user', component: User, meta: { requiresAuth: true } },
    { path: '/admin', component: Admin, alias: ['/Administrator', '/Administer'], meta: { requiresAuth: true, requiresAdmin: true } },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token') || ''
  const role = localStorage.getItem('userRole') || ''
  if (to.meta?.requiresAuth && !token) {
    try {
      localStorage.setItem('authPrompt', 'login-required')
      localStorage.setItem('redirectPath', to.fullPath)
    } catch {}
    return next('/login')
  }
  if (to.meta?.requiresAdmin && role !== 'admin') {
    try {
      localStorage.setItem('authPrompt', 'admin-required')
      localStorage.setItem('redirectPath', to.fullPath)
    } catch {}
    return next('/login')
  }
  return next()
}) 
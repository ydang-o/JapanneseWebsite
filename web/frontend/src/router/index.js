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
    { path: '/user', component: User },
    { path: '/admin', component: Admin, alias: ['/Administrator', '/Administer'] },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
}) 
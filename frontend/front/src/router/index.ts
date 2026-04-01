import { createRouter, createWebHistory } from 'vue-router'

import AboutView from '../views/AboutView.vue'
import AdminView from '../views/AdminView.vue'
import HistoryView from '../views/HistoryView.vue'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'
import ProfileView from '../views/ProfileView.vue'
import SegmentView from '../views/SegmentView.vue'
import { clearAuthStorage, getAccessTokenRole, hasValidAccessToken } from '../utils/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { title: '系统介绍' },
    },
    {
      path: '/segment',
      name: 'segment',
      component: SegmentView,
      meta: { title: '图像分割', requiresAuth: true },
    },
    {
      path: '/history',
      name: 'history',
      component: HistoryView,
      meta: { title: '推理历史', requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: { title: '个人主页', requiresAuth: true },
    },
    {
      path: '/admin',
      name: 'admin',
      component: AdminView,
      meta: { title: '管理后台', requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { title: '登录' },
    },
    {
      path: '/about',
      name: 'about',
      component: AboutView,
      meta: { title: '关于系统' },
    },
  ],
})

router.beforeEach((to) => {
  const hasToken = hasValidAccessToken()
  if (!hasToken) {
    clearAuthStorage()
  }

  if (to.meta.requiresAuth && !hasToken) {
    const redirect = to.fullPath || '/segment'
    return { name: 'login', query: { redirect } }
  }

  if (to.meta.requiresAdmin) {
    const role = getAccessTokenRole()
    if (role !== 'admin') {
      return { name: 'segment' }
    }
  }

  if (to.name === 'login' && hasToken) {
    const role = getAccessTokenRole()
    if (role === 'admin') {
      return '/admin'
    }
    const redirect = typeof to.query.redirect === 'string' ? to.query.redirect : '/segment'
    return redirect
  }

  return true
})

router.afterEach((to) => {
  const title = to.meta.title ? `${to.meta.title} - 自动驾驶图像语义分割系统` : '自动驾驶图像语义分割系统'
  document.title = title
})

export default router

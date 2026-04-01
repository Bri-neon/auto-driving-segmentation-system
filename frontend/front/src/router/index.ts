import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '../views/HomeView.vue'
import SegmentView from '../views/SegmentView.vue'
import AboutView from '../views/AboutView.vue'

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
      meta: { title: '图像分割' },
    },
    {
      path: '/about',
      name: 'about',
      component: AboutView,
      meta: { title: '关于系统' },
    },
  ],
})

router.afterEach((to) => {
  const title = to.meta.title ? `${to.meta.title} - 自动驾驶图像语义分割系统` : '自动驾驶图像语义分割系统'
  document.title = title
})

export default router

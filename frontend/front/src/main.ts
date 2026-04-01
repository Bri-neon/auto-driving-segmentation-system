import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import './style.css'
import { AUTH_UNAUTHORIZED_EVENT } from './utils/auth'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus)

const authStore = useAuthStore(pinia)
authStore.syncSessionFromStorage()
if (authStore.accessToken && !authStore.user) {
  authStore.refreshCurrentUser().catch(() => {
    authStore.logout()
  })
}

if (typeof window !== 'undefined') {
  window.addEventListener(AUTH_UNAUTHORIZED_EVENT, () => {
    authStore.logout()
    if (router.currentRoute.value.path !== '/login') {
      const redirect = router.currentRoute.value.fullPath || '/segment'
      void router.push({ name: 'login', query: { redirect } })
    }
  })
}

app.mount('#app')

import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'
import './style.css'
import { AUTH_UNAUTHORIZED_EVENT } from './utils/auth'
import { initTheme } from './utils/theme'

initTheme()

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

  window.addEventListener('click', (event) => {
    const target = event.target as HTMLElement
    const button = target.closest('.el-button, .ripple-btn') as HTMLElement | null
    if (!button || button.classList.contains('is-disabled')) {
      return
    }

    const rect = button.getBoundingClientRect()
    const diameter = Math.max(rect.width, rect.height)
    const radius = diameter / 2
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    const ripple = document.createElement('span')
    ripple.className = 'button-ripple'
    ripple.style.width = ripple.style.height = `${diameter}px`
    ripple.style.left = `${x - radius}px`
    ripple.style.top = `${y - radius}px`

    const oldRipple = button.querySelector('.button-ripple')
    if (oldRipple) {
      oldRipple.remove()
    }
    button.appendChild(ripple)
  })
}

app.mount('#app')

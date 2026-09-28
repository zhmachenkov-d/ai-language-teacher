import { createApp } from 'vue'
import App from './App.vue'
import { bootstrapTheme } from './composables/useTheme'
import { createAppRouter } from './router'
import './styles/tokens.css'

bootstrapTheme()
createApp(App).use(createAppRouter()).mount('#app')

import { createApp } from 'vue'
import App from './App.vue'
import { bootstrapTheme } from './composables/useTheme'
import './styles/tokens.css'

bootstrapTheme()
createApp(App).mount('#app')

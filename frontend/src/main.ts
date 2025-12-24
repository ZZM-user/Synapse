import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import { create } from 'naive-ui'
import router from './router'

const naive = create()

createApp(App).use(naive).use(router).mount('#app')

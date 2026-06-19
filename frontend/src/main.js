// 前端入口：创建 Vue 应用，挂上路由、状态管理、组件库
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())  // Pinia：全局状态管理（后续放上传进度、纪要数据等）
app.use(router)         // vue-router：页面路由
app.use(ElementPlus)    // Element Plus：组件库，别手搓 UI

app.mount('#app')

// 前端入口：创建 Vue 应用，挂上路由、状态管理、组件库、图标
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import './style.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)

// 全局注册所有 Element Plus 图标（<el-icon><Upload/></el-icon> 直接用）
for (const [name, comp] of Object.entries(ElementPlusIconsVue)) {
  app.component(name, comp)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.mount('#app')

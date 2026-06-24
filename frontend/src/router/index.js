// 路由表：P0 先放两个占位页，后续往里填真内容
import { createRouter, createWebHistory } from 'vue-router'
import UploadView from '../views/UploadView.vue'
import BoardView from '../views/BoardView.vue'

const routes = [
  { path: '/', name: 'upload', component: UploadView },
  { path: '/board', name: 'board', component: BoardView },
]

export default createRouter({
  // BASE_URL 来自 vite 的 base：本地开发是 '/'，生产构建传 --base=/meeting/ 时自动变 '/meeting/'
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// 路由表：P0 先放两个占位页，后续往里填真内容
import { createRouter, createWebHistory } from 'vue-router'
import UploadView from '../views/UploadView.vue'
import BoardView from '../views/BoardView.vue'

const routes = [
  { path: '/', name: 'upload', component: UploadView },
  { path: '/board', name: 'board', component: BoardView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})

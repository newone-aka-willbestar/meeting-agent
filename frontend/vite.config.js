import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Vite 配置：开发服务器 + 构建
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    // 开发代理：前端发到 /api 的请求，由 Vite 转发到后端 8000。
    // 好处：浏览器只跟 5173 打交道，绕开跨域(CORS)；
    // 上线时换成 nginx 反代同样的路径，前端代码不用改。
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // 把前缀 /api 去掉再转发：/api/health -> 后端 /health
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})

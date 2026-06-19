<script setup>
// 上传页（P0 占位）：现在只放一个「测试后端连通」按钮，
// 用来端到端验证 前端 -> Vite 开发代理 -> 后端 这条链路。
// P1 会把它换成真正的音频上传组件。
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const backendStatus = ref('')

async function pingBackend() {
  try {
    const res = await fetch('/api/health')
    const data = await res.json()
    backendStatus.value = JSON.stringify(data)
    ElMessage.success('后端连通：' + backendStatus.value)
  } catch (e) {
    backendStatus.value = '连接失败：' + e
    ElMessage.error(backendStatus.value)
  }
}
</script>

<template>
  <el-card>
    <template #header>上传会议（占位）</template>
    <p>P1 将在这里实现音频上传 → 转写。现在先验证前后端链路。</p>
    <el-button type="primary" @click="pingBackend">测试后端连通</el-button>
    <p v-if="backendStatus" style="margin-top: 12px">{{ backendStatus }}</p>
  </el-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api'

const router = useRouter()
const meetings = ref([])

const stats = computed(() => ({
  total: meetings.value.length,
  done: meetings.value.filter((m) => m.status === 'done').length,
  processing: meetings.value.filter((m) => ['pending', 'processing'].includes(m.status)).length,
}))

async function refresh() {
  meetings.value = await api.listMeetings()
}

async function doUpload(option) {
  try {
    const m = await api.upload(option.file)
    ElMessage.success(`已上传，会议 #${m.id} 正在处理…`)
    await refresh()
    pollUntilDone(m.id)
  } catch (e) {
    ElMessage.error('上传失败：' + e.message)
  }
}

function pollUntilDone(id) {
  const timer = setInterval(async () => {
    const m = await api.getMeeting(id)
    await refresh()
    if (m.status === 'done' || m.status === 'failed') {
      clearInterval(timer)
      if (m.status === 'done') ElMessage.success(`会议 #${id} 处理完成`)
    }
  }, 1500)
}

const statusType = (s) =>
  ({ pending: 'info', processing: 'warning', done: 'success', failed: 'danger' }[s] || 'info')
const statusText = (s) =>
  ({ pending: '排队中', processing: '处理中', done: '已完成', failed: '失败' }[s] || s)

onMounted(refresh)
</script>

<template>
  <!-- 统计卡 -->
  <el-row :gutter="16" class="stats">
    <el-col :span="8"><div class="stat indigo"><div class="num">{{ stats.total }}</div><div class="label">会议总数</div></div></el-col>
    <el-col :span="8"><div class="stat green"><div class="num">{{ stats.done }}</div><div class="label">已完成</div></div></el-col>
    <el-col :span="8"><div class="stat amber"><div class="num">{{ stats.processing }}</div><div class="label">处理中</div></div></el-col>
  </el-row>

  <!-- 上传区 -->
  <el-card class="block">
    <el-upload drag :show-file-list="false" :http-request="doUpload" accept="audio/*">
      <div class="drop">
        <div class="drop-icon">🎙️</div>
        <div class="drop-title">把会议音频拖到这里，或<em>点击选择</em></div>
        <div class="drop-tip">上传后自动转写 → 抽取决策/待办/风险 → 生成纪要与周报</div>
      </div>
    </el-upload>
  </el-card>

  <!-- 会议列表 -->
  <el-card class="block">
    <template #header>
      <div class="card-head">
        <span><el-icon><List /></el-icon> 会议列表</span>
        <el-button size="small" text @click="refresh"><el-icon><Refresh /></el-icon> 刷新</el-button>
      </div>
    </template>
    <el-table :data="meetings" empty-text="还没有会议，先上传一段" style="width: 100%">
      <el-table-column prop="id" label="#" width="64" />
      <el-table-column prop="filename" label="文件名" show-overflow-tooltip />
      <el-table-column label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" effect="light" round>{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="" width="130" align="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" plain :disabled="row.status !== 'done'"
            @click="router.push(`/board?id=${row.id}`)">
            看纪要 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<style scoped>
.stats { margin-bottom: 16px; }
.block { margin-bottom: 16px; }
.card-head { display: flex; justify-content: space-between; align-items: center; }
.card-head .el-icon { vertical-align: -2px; margin-right: 4px; }

.drop { padding: 24px 0; }
.drop-icon { font-size: 46px; }
.drop-title { font-size: 16px; margin-top: 10px; }
.drop-tip { color: #98a2b3; font-size: 13px; margin-top: 6px; }
</style>

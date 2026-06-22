<script setup>
// 上传页：上传音频 → 自动轮询状态 → 列出所有会议，点击进看板
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api'

const router = useRouter()
const meetings = ref([])
const uploading = ref(false)

async function refresh() {
  meetings.value = await api.listMeetings()
}

// el-upload 的自定义上传：拿到文件后调后端
async function doUpload(option) {
  uploading.value = true
  try {
    const m = await api.upload(option.file)
    ElMessage.success(`已上传，会议 #${m.id} 正在处理…`)
    await refresh()
    pollUntilDone(m.id)
  } catch (e) {
    ElMessage.error('上传失败：' + e.message)
  } finally {
    uploading.value = false
  }
}

// 轮询单条会议状态，done 后刷新列表
function pollUntilDone(id) {
  const timer = setInterval(async () => {
    const m = await api.getMeeting(id)
    await refresh()
    if (m.status === 'done' || m.status === 'failed') clearInterval(timer)
  }, 1500)
}

const statusType = (s) =>
  ({ pending: 'info', processing: 'warning', done: 'success', failed: 'danger' }[s] || 'info')

onMounted(refresh)
</script>

<template>
  <el-card>
    <template #header>上传会议音频</template>
    <el-upload drag :show-file-list="false" :http-request="doUpload" accept="audio/*">
      <div style="font-size: 40px">🎙️</div>
      <div class="el-upload__text">把音频拖到这里，或 <em>点击选择</em></div>
      <template #tip>
        <div class="el-upload__tip">上传后会自动转写、抽取决策/待办/风险并生成纪要</div>
      </template>
    </el-upload>
  </el-card>

  <el-card style="margin-top: 16px">
    <template #header>
      会议列表
      <el-button size="small" style="float: right" @click="refresh">刷新</el-button>
    </template>
    <el-table :data="meetings" empty-text="还没有会议，先上传一段">
      <el-table-column prop="id" label="#" width="60" />
      <el-table-column prop="filename" label="文件名" />
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button
            size="small"
            type="primary"
            :disabled="row.status !== 'done'"
            @click="router.push(`/board?id=${row.id}`)"
          >
            看纪要
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

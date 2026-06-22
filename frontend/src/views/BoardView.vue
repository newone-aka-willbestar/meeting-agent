<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import { api } from '../api'

const route = useRoute()
const meetingId = ref(route.query.id ? Number(route.query.id) : null)

const meeting = ref(null)
const ext = ref(null)
const todos = ref([])

const minutesHtml = computed(() => (ext.value?.minutes ? marked.parse(ext.value.minutes) : ''))

async function load() {
  ext.value = null
  meeting.value = null
  if (!meetingId.value) return
  meeting.value = await api.getMeeting(meetingId.value)
  todos.value = await api.listTodos(meetingId.value)
  try {
    ext.value = await api.getExtraction(meetingId.value)
  } catch {
    ext.value = null
  }
}

// 跨会检索
const query = ref('')
const results = ref([])
const searching = ref(false)
async function doSearch() {
  if (!query.value.trim()) return
  searching.value = true
  try {
    const r = await api.search(query.value, 5)
    results.value = r.results
    if (!r.results.length) ElMessage.info('没有找到相关片段')
  } catch (e) {
    ElMessage.error('检索失败：' + e.message)
  } finally {
    searching.value = false
  }
}

onMounted(load)
watch(() => route.query.id, (v) => { meetingId.value = v ? Number(v) : null; load() })
</script>

<template>
  <!-- 跨会检索 -->
  <el-card class="block">
    <div class="search-head">
      <el-icon><Search /></el-icon>
      <b>跨会检索</b>
      <span class="muted">「上次关于 X 我们定了什么」</span>
    </div>
    <el-input v-model="query" size="large" placeholder="比如：支付模块联调谁负责"
      @keyup.enter="doSearch" clearable>
      <template #append>
        <el-button :loading="searching" @click="doSearch" type="primary">检索</el-button>
      </template>
    </el-input>
    <div v-for="(r, i) in results" :key="i" class="hit">
      <el-tag size="small" type="info" effect="plain">会议 {{ r.meeting_id }}</el-tag>
      <span class="hit-text">{{ r.text }}</span>
    </div>
  </el-card>

  <el-empty v-if="!meetingId" description="从『上传会议』点一条进来看纪要" />

  <template v-else>
    <!-- 汇总数字 -->
    <el-row :gutter="16" class="block">
      <el-col :span="6"><div class="stat indigo"><div class="num">{{ ext?.decisions?.length ?? '–' }}</div><div class="label">决策</div></div></el-col>
      <el-col :span="6"><div class="stat green"><div class="num">{{ ext?.todos?.length ?? '–' }}</div><div class="label">待办</div></div></el-col>
      <el-col :span="6"><div class="stat amber"><div class="num">{{ ext?.risks?.length ?? '–' }}</div><div class="label">风险</div></div></el-col>
      <el-col :span="6"><div class="stat slate"><div class="num">{{ ext?.open_questions?.length ?? '–' }}</div><div class="label">待议</div></div></el-col>
    </el-row>

    <el-alert v-if="!ext" class="block" type="info" :closable="false"
      title="抽取还在进行中，稍后刷新页面" show-icon />

    <!-- 三分区 -->
    <el-row :gutter="16" class="block">
      <el-col :span="8">
        <el-card class="cat">
          <template #header><span class="dot d-blue" />决策</template>
          <el-empty v-if="!ext?.decisions?.length" :image-size="48" description="无" />
          <ul v-else><li v-for="(d, i) in ext.decisions" :key="i">{{ d.content || d }}</li></ul>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="cat">
          <template #header><span class="dot d-green" />待办</template>
          <el-empty v-if="!ext?.todos?.length" :image-size="48" description="无" />
          <ul v-else><li v-for="(t, i) in ext.todos" :key="i">
            <b>{{ t.assignee }}</b> · {{ t.content }}
            <el-tag v-if="t.ddl" size="small" type="warning" effect="light">{{ t.ddl }}</el-tag>
          </li></ul>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="cat">
          <template #header><span class="dot d-amber" />风险</template>
          <el-empty v-if="!ext?.risks?.length" :image-size="48" description="无" />
          <ul v-else><li v-for="(r, i) in ext.risks" :key="i">{{ r.description || r }}</li></ul>
        </el-card>
      </el-col>
    </el-row>

    <!-- 纪要 + 周报 -->
    <el-card v-if="ext" class="block">
      <template #header><el-icon><Document /></el-icon> 会议纪要</template>
      <div class="markdown" v-html="minutesHtml" />
      <el-divider />
      <div class="weekly"><b>📅 周报摘要</b><p>{{ ext.weekly_summary }}</p></div>
    </el-card>

    <!-- 待办（任务系统） -->
    <el-card class="block">
      <template #header><el-icon><Tickets /></el-icon> 任务系统 · 待办（会议 #{{ meetingId }}）</template>
      <el-table :data="todos" empty-text="暂无待办">
        <el-table-column prop="assignee" label="负责人" width="110" />
        <el-table-column prop="content" label="内容" show-overflow-tooltip />
        <el-table-column prop="ddl" label="ddl" width="90" />
        <el-table-column label="来源" width="100">
          <template #default="{ row }">
            <el-tag size="small" effect="plain"
              :type="row.source === 'agent' ? 'success' : 'info'">{{ row.source }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 转写原文 -->
    <el-card class="block">
      <template #header><el-icon><Microphone /></el-icon> 转写原文</template>
      <p class="transcript">{{ meeting?.transcript }}</p>
    </el-card>
  </template>
</template>

<style scoped>
.block { margin-bottom: 16px; }
.muted { color: #98a2b3; font-size: 13px; margin-left: 8px; }
.search-head { display: flex; align-items: center; gap: 6px; margin-bottom: 12px; }

.hit { padding: 10px 0; border-bottom: 1px solid #f0f1f5; }
.hit:last-child { border-bottom: none; }
.hit-text { margin-left: 8px; }

.cat :deep(.el-card__header) { display: flex; align-items: center; }
.dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 8px; }
.d-blue { background: #6366f1; }
.d-green { background: #10b981; }
.d-amber { background: #f59e0b; }

ul { margin: 0; padding-left: 18px; }
li { margin: 8px 0; line-height: 1.5; }

.markdown :deep(h1), .markdown :deep(h2) { font-size: 16px; margin: 12px 0 6px; }
.markdown :deep(ul) { padding-left: 20px; }
.weekly p { margin: 6px 0 0; color: #475467; }
.transcript { line-height: 1.8; color: #475467; }
.el-card__header .el-icon { vertical-align: -2px; margin-right: 6px; }
</style>

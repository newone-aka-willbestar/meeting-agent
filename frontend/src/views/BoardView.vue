<script setup>
// 纪要看板：展示某场会议的 决策/待办/风险/待议 + 纪要 + 周报 + 转写；附跨会检索框
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api'

const route = useRoute()
const meetingId = ref(route.query.id ? Number(route.query.id) : null)

const meeting = ref(null)
const ext = ref(null)
const todos = ref([])

async function load() {
  if (!meetingId.value) return
  meeting.value = await api.getMeeting(meetingId.value)
  todos.value = await api.listTodos(meetingId.value)
  try {
    ext.value = await api.getExtraction(meetingId.value)
  } catch {
    ext.value = null // 抽取还没好
  }
}

// ------- 跨会检索 -------
const query = ref('')
const results = ref([])
async function doSearch() {
  if (!query.value.trim()) return
  try {
    const r = await api.search(query.value, 5)
    results.value = r.results
    if (!r.results.length) ElMessage.info('没有找到相关片段')
  } catch (e) {
    ElMessage.error('检索失败：' + e.message)
  }
}

onMounted(load)
watch(() => route.query.id, (v) => { meetingId.value = v ? Number(v) : null; load() })
</script>

<template>
  <!-- 跨会检索 -->
  <el-card style="margin-bottom: 16px">
    <template #header>🔎 跨会检索（上次关于 X 我们定了什么）</template>
    <el-input v-model="query" placeholder="比如：支付模块联调谁负责" @keyup.enter="doSearch">
      <template #append><el-button @click="doSearch">检索</el-button></template>
    </el-input>
    <div v-for="(r, i) in results" :key="i" class="hit">
      <el-tag size="small">会议 {{ r.meeting_id }}</el-tag>
      <span style="margin-left: 8px">{{ r.text }}</span>
    </div>
  </el-card>

  <el-empty v-if="!meetingId" description="从『上传会议』点一条进来看纪要" />

  <template v-else>
    <!-- 三分区：决策 / 待办 / 风险 -->
    <el-row :gutter="16">
      <el-col :span="8">
        <el-card><template #header>✅ 决策</template>
          <el-empty v-if="!ext?.decisions?.length" :image-size="60" description="无" />
          <ul><li v-for="(d, i) in ext?.decisions" :key="i">{{ d.content || d }}</li></ul>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card><template #header>📋 待办</template>
          <el-empty v-if="!ext?.todos?.length" :image-size="60" description="无" />
          <ul><li v-for="(t, i) in ext?.todos" :key="i">
            <b>{{ t.assignee }}</b>：{{ t.content }}
            <el-tag v-if="t.ddl" size="small" type="warning">{{ t.ddl }}</el-tag>
          </li></ul>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card><template #header>⚠️ 风险</template>
          <el-empty v-if="!ext?.risks?.length" :image-size="60" description="无" />
          <ul><li v-for="(r, i) in ext?.risks" :key="i">{{ r.description || r }}</li></ul>
        </el-card>
      </el-col>
    </el-row>

    <!-- 纪要 + 周报 -->
    <el-card style="margin-top: 16px">
      <template #header>📝 会议纪要 / 周报</template>
      <el-alert v-if="!ext" type="info" :closable="false"
        title="抽取还在进行中，稍后刷新" />
      <template v-else>
        <pre class="minutes">{{ ext.minutes }}</pre>
        <el-divider />
        <b>周报摘要：</b>{{ ext.weekly_summary }}
      </template>
    </el-card>

    <!-- 待办（含 agent 自动落库的） -->
    <el-card style="margin-top: 16px">
      <template #header>🗂️ 任务系统里的待办（meeting #{{ meetingId }}）</template>
      <el-table :data="todos" empty-text="暂无">
        <el-table-column prop="assignee" label="负责人" width="100" />
        <el-table-column prop="content" label="内容" />
        <el-table-column prop="ddl" label="ddl" width="90" />
        <el-table-column prop="source" label="来源" width="90" />
      </el-table>
    </el-card>

    <!-- 转写原文 -->
    <el-card style="margin-top: 16px">
      <template #header>🎧 转写原文</template>
      <p>{{ meeting?.transcript }}</p>
    </el-card>
  </template>
</template>

<style scoped>
.hit { padding: 8px 0; border-bottom: 1px solid var(--el-border-color-lighter); }
.minutes { white-space: pre-wrap; font-family: inherit; margin: 0; }
ul { margin: 0; padding-left: 18px; }
li { margin: 6px 0; }
</style>

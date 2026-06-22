<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeIndex = computed(() => route.path)
const pageTitle = computed(
  () => ({ '/': '上传会议', '/board': '纪要看板' }[route.path] || '会议数字员工'),
)
</script>

<template>
  <el-container class="app">
    <!-- 左侧导航 -->
    <el-aside width="232px" class="sidebar">
      <div class="brand">
        <span class="brand-icon">🎙️</span>
        <div>
          <div class="brand-name">会议数字员工</div>
          <div class="brand-sub">Meeting Intelligence</div>
        </div>
      </div>

      <el-menu
        :default-active="activeIndex"
        router
        class="menu"
        background-color="transparent"
        text-color="#c7cdd9"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/">
          <el-icon><UploadFilled /></el-icon><span>上传会议</span>
        </el-menu-item>
        <el-menu-item index="/board">
          <el-icon><Document /></el-icon><span>纪要看板</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-foot">
        <el-icon><Cpu /></el-icon> 抽取 · 检索 · MCP
      </div>
    </el-aside>

    <!-- 右侧内容 -->
    <el-container>
      <el-header class="topbar">
        <span class="topbar-title">{{ pageTitle }}</span>
        <el-tag size="small" effect="plain" round>本地 Demo</el-tag>
      </el-header>
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.app { height: 100vh; }

.sidebar {
  background: linear-gradient(180deg, #1e1b4b 0%, #312e81 100%);
  display: flex;
  flex-direction: column;
  padding: 0;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 22px 20px;
  color: #fff;
}
.brand-icon { font-size: 26px; }
.brand-name { font-weight: 700; font-size: 16px; }
.brand-sub { font-size: 11px; color: #a5b4fc; letter-spacing: 0.5px; }

.menu { border: none; padding: 8px 12px; }
.menu .el-menu-item {
  border-radius: 10px;
  margin: 4px 0;
  height: 46px;
}
.menu .el-menu-item.is-active { background: rgba(255, 255, 255, 0.14); }
.menu .el-menu-item:hover { background: rgba(255, 255, 255, 0.08); }

.sidebar-foot {
  margin-top: auto;
  padding: 18px 22px;
  color: #a5b4fc;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.topbar {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #eef0f4;
}
.topbar-title { font-size: 18px; font-weight: 600; }
.main { padding: 24px; }
</style>

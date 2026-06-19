<script setup>
// 根组件：一个带顶部导航的整体布局，内容区由路由决定
import { useRoute } from 'vue-router'
import { computed } from 'vue'

const route = useRoute()
// 当前高亮的菜单项跟随路由路径
const activeIndex = computed(() => route.path)
</script>

<template>
  <el-container>
    <el-header>
      <div class="logo">🎙️ 会议数字员工</div>
      <el-menu :default-active="activeIndex" mode="horizontal" router :ellipsis="false">
        <el-menu-item index="/">上传会议</el-menu-item>
        <el-menu-item index="/board">纪要看板</el-menu-item>
      </el-menu>
    </el-header>
    <el-main>
      <!-- 路由匹配到的页面渲染在这里 -->
      <router-view />
    </el-main>
  </el-container>
</template>

<style>
.el-header {
  display: flex;
  align-items: center;
  gap: 24px;
  border-bottom: 1px solid var(--el-border-color);
}
.logo {
  font-weight: 600;
  font-size: 18px;
  white-space: nowrap;
}
</style>

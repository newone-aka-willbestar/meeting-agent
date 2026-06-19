<script setup>
// 纪要看板页（P0 占位）：P3 会做成「决策 / 待办 / 风险」三分区，
// 待办可点回原话出处。现在先放三个空列示意结构。
</script>

<template>
  <el-row :gutter="16">
    <el-col :span="8">
      <el-card><template #header>✅ 决策</template>（占位）</el-card>
    </el-col>
    <el-col :span="8">
      <el-card><template #header>📋 待办</template>（占位）</el-card>
    </el-col>
    <el-col :span="8">
      <el-card><template #header>⚠️ 风险</template>（占位）</el-card>
    </el-col>
  </el-row>
</template>

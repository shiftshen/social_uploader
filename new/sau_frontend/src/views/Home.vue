<template>
  <div class="page">
    <div class="page-header">
      <h1>{{ title }}</h1>
    </div>
    <el-card class="card">
      <el-empty :description="description" />
    </el-card>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: '页面'
  },
  description: {
    type: String,
    default: '功能开发中'
  }
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.page {
  .page-header {
    margin-bottom: 20px;

    h1 {
      font-size: 24px;
      font-weight: 500;
      color: $text-primary;
      margin: 0;
    }
  }

  .card {
    padding: 30px 0;
  }
}
</style>

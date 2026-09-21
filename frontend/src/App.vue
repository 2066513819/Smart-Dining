<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// 简化版本，移除过渡动画
</script>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  height: 100%;
}

body {
  min-height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background-color: #f5f7fa;
  color: #1f2937;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  width: 100%;
  min-height: 100vh;
  margin: 0;
  padding: 0;
}

/* 全局链接样式 */
a {
  color: #667eea;
  text-decoration: none;
  transition: color 0.2s ease;
}

a:hover {
  color: #764ba2;
}

/* 全局按钮样式 */
button {
  cursor: pointer;
  font-family: inherit;
}

/* 全局表单元素样式 */
input, select, textarea {
  font-family: inherit;
}

/* ========================================
   页面过渡动画
   ======================================== */

/* 认证页面淡入淡出 */
.auth-fade-enter-active,
.auth-fade-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.auth-fade-enter-from {
  opacity: 0;
  transform: scale(0.98);
}

.auth-fade-leave-to {
  opacity: 0;
  transform: scale(1.02);
}

/* 页面滑动过渡 */
.page-slide-enter-active,
.page-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.page-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.page-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* ========================================
   Element Plus 全局样式覆盖
   ======================================== */

/* 主按钮渐变色 */
.el-button--primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(102, 126, 234, 0.35);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.el-button--primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.45) !important;
}

.el-button--primary:active {
  transform: translateY(0);
}

/* 成功按钮 */
.el-button--success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35);
}

.el-button--success:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.45) !important;
}

/* 警告按钮 */
.el-button--warning {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(245, 158, 11, 0.35);
}

.el-button--warning:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(245, 158, 11, 0.45) !important;
}

/* 危险按钮 */
.el-button--danger {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(239, 68, 68, 0.35);
}

.el-button--danger:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.45) !important;
}

/* 信息按钮 */
.el-button--info {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%) !important;
  border: none !important;
}

/* 卡片 */
.el-card {
  border-radius: 16px !important;
  border: 1px solid rgba(0, 0, 0, 0.05) !important;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  overflow: hidden;
}

.el-card:hover {
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.05) !important;
}

.el-card__header {
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05) !important;
  padding: 16px 20px !important;
}

.el-card__body {
  padding: 20px !important;
}

/* 标签 */
.el-tag {
  border-radius: 20px !important;
  font-weight: 500;
  padding: 0 12px !important;
  height: 26px !important;
  line-height: 24px !important;
  border: none !important;
}

.el-tag--primary {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
  color: #667eea;
}

.el-tag--success {
  background: rgba(16, 185, 129, 0.12);
  color: #059669;
}

.el-tag--warning {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
}

.el-tag--danger {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
}

.el-tag--info {
  background: rgba(107, 114, 128, 0.12);
  color: #4b5563;
}

/* 输入框 */
.el-input__wrapper {
  border-radius: 10px !important;
  box-shadow: 0 0 0 1px #e5e7eb inset !important;
  transition: all 0.2s ease !important;
}

.el-input__wrapper:hover {
  box-shadow: 0 0 0 1px #c7d2fe inset !important;
}

.el-input__wrapper.is-focus {
  box-shadow: 0 0 0 2px #667eea inset, 0 0 0 4px rgba(102, 126, 234, 0.1) !important;
}

/* 选择器 */
.el-select__wrapper {
  border-radius: 10px !important;
}

/* 对话框 */
.el-dialog {
  border-radius: 20px !important;
  overflow: hidden;
}

.el-dialog__header {
  padding: 20px 24px 16px !important;
  border-bottom: 1px solid #f3f4f6;
}

.el-dialog__title {
  font-weight: 600 !important;
  font-size: 18px !important;
  color: #1f2937 !important;
}

.el-dialog__body {
  padding: 20px 24px !important;
}

.el-dialog__footer {
  padding: 16px 24px 20px !important;
  border-top: 1px solid #f3f4f6;
}

/* 消息提示 */
.el-message {
  border-radius: 12px !important;
  border: none !important;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15) !important;
  padding: 12px 20px !important;
}

.el-message--success {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%) !important;
}

.el-message--warning {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%) !important;
}

.el-message--error {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%) !important;
}

.el-message--info {
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%) !important;
}

/* 分页 */
.el-pagination {
  --el-pagination-button-bg-color: #f3f4f6;
  --el-pagination-hover-color: #667eea;
}

.el-pager li {
  border-radius: 8px !important;
  font-weight: 500;
}

.el-pager li.is-active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}

/* 表格 */
.el-table {
  border-radius: 12px !important;
  overflow: hidden;
}

.el-table__header th {
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%) !important;
  font-weight: 600 !important;
  color: #374151 !important;
}

.el-table__row:hover > td {
  background: rgba(102, 126, 234, 0.04) !important;
}

/* 加载动画 */
.el-loading-spinner .circular {
  width: 48px !important;
  height: 48px !important;
}

.el-loading-spinner .path {
  stroke: #667eea !important;
}

/* 空状态 */
.el-empty__description {
  color: #9ca3af;
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f3f4f6;
  border-radius: 10px;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #c7d2fe 0%, #a78bfa 100%);
  border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, #a78bfa 0%, #8b5cf6 100%);
}

/* 选中文本 */
::selection {
  background: rgba(102, 126, 234, 0.2);
  color: #1f2937;
}

/* ========================================
   工具类
   ======================================== */

/* 渐变文字 */
.gradient-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 渐变背景 */
.gradient-bg {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 卡片悬浮效果 */
.hover-lift {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.hover-lift:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}
</style>

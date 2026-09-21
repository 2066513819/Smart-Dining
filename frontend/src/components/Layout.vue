<template>
  <div class="layout-container">
    <!-- 左侧菜单 -->
    <el-aside :width="isCollapse ? '72px' : '240px'" class="layout-aside">
      <!-- Logo区域 -->
      <div class="logo-container">
        <div class="logo" v-if="!isCollapse">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none">
              <defs>
                <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#667eea"/>
                  <stop offset="100%" stop-color="#764ba2"/>
                </linearGradient>
              </defs>
              <circle cx="12" cy="12" r="10" fill="url(#logoGradient)"/>
              <path d="M8 11c0-2.21 1.79-4 4-4s4 1.79 4 4c0 1.1-.45 2.1-1.17 2.83L12 17l-2.83-3.17A3.99 3.99 0 018 11z" fill="white" opacity="0.9"/>
            </svg>
          </div>
          <div class="logo-text">
            <span class="brand-name">餐饮推荐</span>
            <span class="brand-sub">Smart Nutrition</span>
          </div>
        </div>
        <div class="logo-mini" v-else>
          <svg viewBox="0 0 24 24" fill="none">
            <defs>
              <linearGradient id="logoGradientMini" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#667eea"/>
                <stop offset="100%" stop-color="#764ba2"/>
              </linearGradient>
            </defs>
            <circle cx="12" cy="12" r="10" fill="url(#logoGradientMini)"/>
            <path d="M8 11c0-2.21 1.79-4 4-4s4 1.79 4 4c0 1.1-.45 2.1-1.17 2.83L12 17l-2.83-3.17A3.99 3.99 0 018 11z" fill="white" opacity="0.9"/>
          </svg>
        </div>
      </div>
      
      <!-- 菜单导航 -->
      <el-scrollbar class="menu-scrollbar">
        <el-menu
          :default-active="activeMenu"
          class="layout-menu"
          mode="vertical"
          :collapse="isCollapse"
          :router="true"
          @select="handleMenuSelect"
        >
          <!-- 首页 -->
          <el-menu-item index="/home">
            <template #title>
              <div class="menu-item-content">
                <div class="menu-icon">
                  <svg viewBox="0 0 24 24" fill="none">
                    <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8h5z" fill="currentColor"/>
                  </svg>
                </div>
                <span class="menu-text">首页</span>
              </div>
            </template>
          </el-menu-item>
          
          <!-- 菜谱管理 -->
          <el-sub-menu index="recipe-management">
            <template #title>
              <div class="menu-item-content">
                <div class="menu-icon">
                  <svg viewBox="0 0 24 24" fill="none">
                    <path d="M8.1 13.34l2.83-2.83L3.91 3.5c-1.56 1.56-1.56 4.09 0 5.66l4.19 4.18zm6.78-1.81c1.53.71 3.68.21 5.27-1.38 1.91-1.91 2.28-4.65.81-6.12-1.46-1.46-4.2-1.1-6.12.81-1.59 1.59-2.09 3.74-1.38 5.27L3.7 19.87l1.41 1.41L12 14.41l6.88 6.88 1.41-1.41L13.41 13l1.47-1.47z" fill="currentColor"/>
                  </svg>
                </div>
                <span class="menu-text">菜谱管理</span>
              </div>
            </template>
            
            <el-menu-item index="/recommendation">
              <span class="menu-text">菜谱制定</span>
            </el-menu-item>
            
            <el-menu-item index="/meal-rules">
              <span class="menu-text">餐饮设置</span>
            </el-menu-item>
            
            <el-menu-item index="/history-plans">
              <span class="menu-text">历史菜谱</span>
            </el-menu-item>
            
            <el-menu-item index="/recipe-method">
              <span class="menu-text">制作方法</span>
            </el-menu-item>
          </el-sub-menu>

          <!-- 菜品管理 -->
          <el-sub-menu index="dish-management-sub">
            <template #title>
              <div class="menu-item-content">
                <div class="menu-icon">
                  <svg viewBox="0 0 24 24" fill="none">
                    <path d="M11 9H9V2H7v7H5V2H3v7c0 2.12 1.66 3.84 3.75 3.97V22h2.5v-9.03C11.34 12.84 13 11.12 13 9V2h-2v7zm5-3v8h2.5v8H21V2c-2.76 0-5 2.24-5 4z" fill="currentColor"/>
                  </svg>
                </div>
                <span class="menu-text">菜品管理</span>
              </div>
            </template>
            
            <el-menu-item index="/dish-management">
              <span class="menu-text">菜品列表</span>
            </el-menu-item>
            
            <el-menu-item index="/ingredient-cost">
              <span class="menu-text">食材成本</span>
            </el-menu-item>
            
            <el-menu-item index="/ingredient-nutrition">
              <span class="menu-text">食材营养</span>
            </el-menu-item>
          </el-sub-menu>
          
          <!-- 管理员面板（仅管理员可见） -->
          <el-menu-item v-if="authStore.user?.role === 'admin'" index="/admin">
            <template #title>
              <div class="menu-item-content">
                <div class="menu-icon">
                  <svg viewBox="0 0 24 24" fill="none">
                    <path d="M12 2l3 7h7l-5.5 4 2.5 7-6-4.5L7 20l2.5-7L4 9h7l3-7z" fill="currentColor"/>
                  </svg>
                </div>
                <span class="menu-text">管理员面板</span>
              </div>
            </template>
          </el-menu-item>
        </el-menu>
      </el-scrollbar>
      
      <!-- 菜单折叠按钮 -->
      <div class="collapse-btn" @click="toggleCollapse" :title="isCollapse ? '展开菜单' : '折叠菜单'">
        <svg viewBox="0 0 24 24" fill="none" :class="{ 'rotate-180': isCollapse }">
          <path d="M15.41 7.41L14 6l-6 6 6 6 1.41-1.41L10.83 12l4.58-4.59z" fill="currentColor"/>
        </svg>
      </div>
    </el-aside>

    <!-- 右侧内容区域 -->
    <div class="layout-main">
      <!-- 顶部导航栏 -->
      <el-header class="layout-header">
        <div class="header-left">
          <!-- 移动端菜单按钮 -->
          <button
            class="mobile-menu-btn"
            @click="toggleMobileMenu"
            aria-label="Toggle menu"
          >
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z" fill="currentColor"/>
            </svg>
          </button>
          
          <!-- 面包屑导航 -->
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item :to="{ path: '/' }">
              <svg class="breadcrumb-home" viewBox="0 0 24 24" fill="none">
                <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8h5z" fill="currentColor"/>
              </svg>
            </el-breadcrumb-item>
            <el-breadcrumb-item v-for="item in breadcrumbItems" :key="item.path" :to="item.path">
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <!-- 全屏切换 -->
          <button 
            class="header-btn" 
            @click="toggleFullscreen" 
            :title="isFullscreen ? '退出全屏' : '全屏'"
          >
            <svg v-if="isFullscreen" viewBox="0 0 24 24" fill="none">
              <path d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z" fill="currentColor"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none">
              <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z" fill="currentColor"/>
            </svg>
          </button>
          
          <!-- 用户信息下拉菜单 -->
          <el-dropdown trigger="click" class="user-dropdown">
            <div class="user-info">
              <el-avatar :size="38" :src="userAvatar" class="user-avatar">
                <span class="avatar-text">{{ username?.charAt(0)?.toUpperCase() || 'U' }}</span>
              </el-avatar>
              <div class="user-details" v-if="!isCollapse">
                <div class="username">{{ username }}</div>
                <div class="user-role">{{ userRole }}</div>
              </div>
              <svg class="arrow-down" viewBox="0 0 24 24" fill="none">
                <path d="M7 10l5 5 5-5H7z" fill="currentColor"/>
              </svg>
            </div>
            <template #dropdown>
              <el-dropdown-menu class="user-menu">
                <!-- 个人中心 -->
                <el-dropdown-item @click="router.push('/profile')">
                  <svg viewBox="0 0 24 24" fill="none">
                    <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" fill="currentColor"/>
                  </svg>
                  <span>个人中心</span>
                </el-dropdown-item>
                
                <!-- 账户设置 -->
                <el-dropdown-item @click="router.push('/settings')">
                  <svg viewBox="0 0 24 24" fill="none">
                    <path d="M19.14 12.94c.04-.31.06-.63.06-.94 0-.31-.02-.63-.06-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z" fill="currentColor"/>
                  </svg>
                  <span>账户设置</span>
                </el-dropdown-item>
                
                <!-- 修改密码 -->
                <el-dropdown-item @click="router.push('/change-password')">
                  <svg viewBox="0 0 24 24" fill="none">
                    <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z" fill="currentColor"/>
                  </svg>
                  <span>修改密码</span>
                </el-dropdown-item>
                
                <!-- 分割线 -->
                <el-dropdown-item divided @click="handleLogout" class="logout-item">
                  <svg viewBox="0 0 24 24" fill="none">
                    <path d="M17 7l-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5-5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z" fill="currentColor"/>
                  </svg>
                  <span>退出登录</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主内容区 -->
      <el-main class="layout-content">
        <transition name="page-fade" mode="out-in">
          <router-view v-slot="{ Component }">
            <component :is="Component" />
          </router-view>
        </transition>
      </el-main>
      
      <!-- 页脚 -->
      <el-footer class="layout-footer">
        <div class="footer-content">
          <span>© 2025 餐饮推荐系统. All Rights Reserved.</span>
          <div class="footer-links">
            <a href="#" class="footer-link">帮助中心</a>
            <span class="divider">|</span>
            <a href="#" class="footer-link">联系我们</a>
            <span class="divider">|</span>
            <a href="#" class="footer-link">隐私政策</a>
          </div>
        </div>
      </el-footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 菜单折叠状态
const isCollapse = ref(false)

// 移动端菜单状态
const isMobileMenuOpen = ref(false)

// 全屏状态
const isFullscreen = ref(false)

// 切换菜单折叠状态
const toggleCollapse = async () => {
  isCollapse.value = !isCollapse.value
  // 强制通知当前页图表/Canvas 重绘：侧边栏宽度变化不一定触发 window.resize
  await nextTick()
  window.dispatchEvent(new Event('layout-resize'))
  // 兼容：部分页面只监听 resize 事件
  window.dispatchEvent(new Event('resize'))
  // 给过渡动画留一点时间，确保宽高已经稳定
  setTimeout(() => {
    window.dispatchEvent(new Event('layout-resize'))
    window.dispatchEvent(new Event('resize'))
  }, 160)
}

// 切换移动端菜单
const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

// 切换全屏
const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(err => {
      console.error('Failed to enable fullscreen:', err)
    })
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen()
    }
  }
}

// 菜单点击处理
const handleMenuSelect = (index: string) => {
  console.log('Menu selected:', index)
}

// 监听全屏变化
const handleFullscreenChange = () => {
  isFullscreen.value = !!document.fullscreenElement
}

// 当前激活的菜单
const activeMenu = computed(() => {
  return route.path
})

// 面包屑导航
  const breadcrumbItems = computed(() => {
    const pathMap: Record<string, string> = {
      '/home': '首页',
      '/recommendation': '菜谱制定',
      '/history-plans': '历史菜谱',
      '/recipe-method': '制作方法',
      '/dish-analysis': '菜品分析',
      '/dish-management': '菜品列表',
      '/ingredient-cost': '食材成本',
      '/add-dish': '添加菜品',
      '/admin': '管理员面板',
      '/profile': '个人中心',
      '/settings': '账户设置',
    '/change-password': '修改密码',
    '/auth-test': '认证测试'
  }
  
  const items = []
  const pathSegments = route.path.split('/').filter(segment => segment)
  
  let currentPath = ''
  for (const segment of pathSegments) {
    currentPath += `/${segment}`
    if (pathMap[currentPath]) {
      items.push({
        path: currentPath,
        title: pathMap[currentPath]
      })
    }
  }
  
  return items
})

// 用户信息
const username = computed(() => {
  return authStore.user?.username || '未登录'
})

const userAvatar = computed(() => {
  // 使用统一的默认头像
  return 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'
  // return authStore.user?.avatar || ''
})

const userRole = computed(() => {
  return authStore.user?.role || '普通用户'
})

// 退出登录
const handleLogout = () => {
  // 移除智能体小助手显示类
  document.body.classList.remove('show-chatbot')
  authStore.logout()
  router.push('/login')
}

// 监听窗口大小变化
const handleResize = () => {
  if (window.innerWidth < 768) {
    isCollapse.value = true
  }
}

// 生命周期钩子
  onMounted(async () => {
     // 开启智能体小助手显示
     document.body.classList.add('show-chatbot')
     // 确保用户信息已加载
     if (!authStore.user) {
       await authStore.fetchUser()
     }
     // 监听全屏变化
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
  // 初始检查窗口大小
  handleResize()
})

onBeforeUnmount(() => {
  // 移除智能体小助手显示类
  document.body.classList.remove('show-chatbot')
  // 移除事件监听器
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
/* 全局布局容器 */
.layout-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background-color: #f5f7fa;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* 左侧菜单 */
.layout-aside {
  background: linear-gradient(180deg, #1e1e2d 0%, #1a1a27 100%);
  color: white;
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 100;
}

/* Logo样式 */
.logo-container {
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
}

.logo-icon svg {
  width: 100%;
  height: 100%;
  filter: drop-shadow(0 2px 8px rgba(102, 126, 234, 0.4));
}

.logo-mini {
  width: 40px;
  height: 40px;
}

.logo-mini svg {
  width: 100%;
  height: 100%;
  filter: drop-shadow(0 2px 8px rgba(102, 126, 234, 0.4));
}

.logo-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.brand-name {
  font-size: 17px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #a78bfa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 0.5px;
}

.brand-sub {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* 菜单滚动区域 */
.menu-scrollbar {
  flex: 1;
  padding: 16px 0;
}

/* 菜单样式 */
.layout-menu {
  border: none;
  background: transparent;
  padding: 0 12px;
}

:deep(.el-menu) {
  background: transparent;
  border: none;
}

:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  height: 50px;
  line-height: 50px;
  margin: 4px 0;
  padding: 0 !important;
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.65);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background: rgba(102, 126, 234, 0.15) !important;
  color: #fff !important;
}

:deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.9) 0%, rgba(118, 75, 162, 0.9) 100%);
  color: #fff;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

:deep(.el-sub-menu.is-active .el-sub-menu__title) {
  color: #fff !important;
}

:deep(.el-sub-menu .el-menu-item) {
  padding-left: 48px !important;
  height: 45px;
  line-height: 45px;
}

.menu-item-content {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px;
  width: 100%;
  height: 100%;
}

.menu-icon {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.menu-icon svg {
  width: 100%;
  height: 100%;
}

.menu-text {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
}

.menu-badge {
  padding: 2px 8px;
  border-radius: 20px;
  font-size: 10px;
  font-weight: 600;
  margin-left: auto;
}

.menu-badge.ai {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

/* 折叠状态 */
:deep(.el-menu--collapse) {
  width: 100%;
}

:deep(.el-menu--collapse .el-menu-item) {
  padding: 0 !important;
  justify-content: center;
}

:deep(.el-menu--collapse) .menu-item-content {
  justify-content: center;
  padding: 0;
}

:deep(.el-menu--collapse) .menu-text,
:deep(.el-menu--collapse) .menu-badge {
  display: none;
}

/* 折叠按钮 */
.collapse-btn {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.collapse-btn:hover {
  transform: translateX(-50%) scale(1.1);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
}

.collapse-btn svg {
  width: 20px;
  height: 20px;
  color: white;
  transition: transform 0.3s ease;
}

.collapse-btn svg.rotate-180 {
  transform: rotate(180deg);
}

/* 主内容区域 */
.layout-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #f5f7fa;
}

/* 顶部导航栏 */
.layout-header {
  height: 64px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.9) 100%);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  z-index: 99;
}

/* 移动端菜单按钮 */
.mobile-menu-btn {
  display: none;
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  cursor: pointer;
  border-radius: 8px;
  margin-right: 12px;
  transition: background 0.2s ease;
}

.mobile-menu-btn:hover {
  background: rgba(102, 126, 234, 0.1);
}

.mobile-menu-btn svg {
  width: 24px;
  height: 24px;
  color: #4b5563;
}

/* 左侧头部区域 */
.header-left {
  display: flex;
  align-items: center;
}

/* 面包屑导航 */
.breadcrumb {
  font-size: 14px;
}

.breadcrumb-home {
  width: 16px;
  height: 16px;
  color: #9ca3af;
  vertical-align: middle;
}

:deep(.el-breadcrumb__inner a:hover) {
  color: #667eea;
}

/* 右侧头部区域 */
.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 头部按钮 */
.header-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  cursor: pointer;
  border-radius: 10px;
  transition: all 0.2s ease;
  color: #6b7280;
}

.header-btn:hover {
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
}

.header-btn svg {
  width: 22px;
  height: 22px;
}

/* 用户信息 */
.user-dropdown {
  margin-left: 8px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 12px;
  transition: all 0.2s ease;
}

.user-info:hover {
  background: rgba(102, 126, 234, 0.08);
}

.user-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.avatar-text {
  font-size: 16px;
  font-weight: 600;
  color: white;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.username {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.user-role {
  font-size: 12px;
  color: #9ca3af;
}

.arrow-down {
  width: 20px;
  height: 20px;
  color: #9ca3af;
  transition: transform 0.2s ease;
}

/* 用户下拉菜单 */
:deep(.user-menu) {
  padding: 8px;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
  color: #4b5563;
  transition: all 0.2s ease;
}

:deep(.el-dropdown-menu__item svg) {
  width: 18px;
  height: 18px;
  color: #9ca3af;
}

:deep(.el-dropdown-menu__item:hover) {
  background: rgba(102, 126, 234, 0.08);
  color: #667eea;
}

:deep(.el-dropdown-menu__item:hover svg) {
  color: #667eea;
}

:deep(.logout-item) {
  color: #ef4444;
}

:deep(.logout-item:hover) {
  background: rgba(239, 68, 68, 0.08);
  color: #ef4444;
}

:deep(.logout-item svg) {
  color: #ef4444;
}

/* 主内容区 */
.layout-content {
  flex: 1;
  padding: 24px;
  background-color: #f5f7fa;
  overflow-y: auto;
}

/* 页面切换动画 */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: all 0.25s ease-out;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}

/* 页脚 */
.layout-footer {
  height: 48px;
  background: white;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #9ca3af;
}

.footer-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  max-width: 1200px;
  padding: 0 24px;
}

.footer-links {
  display: flex;
  align-items: center;
  gap: 8px;
}

.footer-link {
  color: #6b7280;
  text-decoration: none;
  transition: color 0.2s ease;
}

.footer-link:hover {
  color: #667eea;
}

.divider {
  color: #e5e7eb;
}

/* 滚动条样式 */
.layout-content::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.layout-content::-webkit-scrollbar-track {
  background: transparent;
}

.layout-content::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #c7d2fe 0%, #a78bfa 100%);
  border-radius: 10px;
}

.layout-content::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, #a78bfa 0%, #8b5cf6 100%);
}

/* 响应式 */
@media (max-width: 768px) {
  .mobile-menu-btn {
    display: flex;
  }
  
  .layout-content {
    padding: 16px;
  }
  
  .user-details,
  .arrow-down {
    display: none;
  }
  
  .footer-links {
    display: none;
  }
  
  .layout-header {
    padding: 0 16px;
  }
}

@media (max-width: 576px) {
  .layout-header {
    padding: 0 12px;
  }
  
  .layout-content {
    padding: 12px;
  }
}
</style>

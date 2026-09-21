<template>
  <div class="register-container">
    <!-- 动态背景 -->
    <div class="animated-bg">
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
        <div class="shape shape-4"></div>
        <div class="shape shape-5"></div>
        <div class="shape shape-6"></div>
      </div>
    </div>

    <!-- 注册卡片 -->
    <div class="register-card">
      <!-- Logo 区域 -->
      <div class="logo-section">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" fill="url(#gradient1)"/>
            <path d="M11 7h2v6h-2V7zm0 8h2v2h-2v-2z" fill="white"/>
            <path d="M8 11c0-2.21 1.79-4 4-4s4 1.79 4 4c0 1.1-.45 2.1-1.17 2.83L12 17l-2.83-3.17A3.99 3.99 0 018 11z" fill="white" opacity="0.9"/>
            <defs>
              <linearGradient id="gradient1" x1="2" y1="2" x2="22" y2="22">
                <stop offset="0%" stop-color="#667eea"/>
                <stop offset="100%" stop-color="#764ba2"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h1 class="app-title">创建账户</h1>
        <p class="app-subtitle">加入我们，开启智能营养管理之旅</p>
      </div>

      <!-- 步骤指示器 -->
      <div class="step-indicator">
        <div class="step" :class="{ active: currentStep >= 1, completed: currentStep > 1 }">
          <span class="step-number">1</span>
          <span class="step-label">账户信息</span>
        </div>
        <div class="step-line" :class="{ active: currentStep > 1 }"></div>
        <div class="step" :class="{ active: currentStep >= 2 }">
          <span class="step-number">2</span>
          <span class="step-label">个人资料</span>
        </div>
      </div>

      <!-- 注册表单 -->
      <form @submit.prevent="handleRegister" class="register-form">
        <!-- 步骤1: 账户信息 -->
        <div class="form-step" v-show="currentStep === 1">
          <div class="form-group">
            <label for="username">
              <svg class="input-icon" viewBox="0 0 24 24" fill="none">
                <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" fill="currentColor"/>
              </svg>
              用户名
            </label>
            <div class="input-wrapper">
              <input 
                type="text" 
                id="username" 
                v-model="userData.username" 
                required 
                placeholder="请输入用户名（3-50个字符）"
                minlength="3"
                maxlength="50"
              >
            </div>
          </div>

          <div class="form-group">
            <label for="password">
              <svg class="input-icon" viewBox="0 0 24 24" fill="none">
                <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z" fill="currentColor"/>
              </svg>
              密码
            </label>
            <div class="input-wrapper">
              <input 
                :type="showPassword ? 'text' : 'password'" 
                id="password" 
                v-model="userData.password" 
                required 
                placeholder="请输入密码（至少6个字符）"
                minlength="6"
              >
              <button 
                type="button" 
                class="toggle-password" 
                @click="showPassword = !showPassword"
                tabindex="-1"
              >
                <svg v-if="showPassword" viewBox="0 0 24 24" fill="none">
                  <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z" fill="currentColor"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none">
                  <path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z" fill="currentColor"/>
                </svg>
              </button>
            </div>
            <!-- 密码强度指示器 -->
            <div class="password-strength" v-if="userData.password">
              <div class="strength-bar">
                <div class="strength-level" :style="{ width: passwordStrength.width }" :class="passwordStrength.class"></div>
              </div>
              <span class="strength-text" :class="passwordStrength.class">{{ passwordStrength.text }}</span>
            </div>
          </div>

          <button type="button" class="next-btn" @click="nextStep" :disabled="!canProceed">
            下一步
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8-8-8z" fill="currentColor"/>
            </svg>
          </button>
        </div>

        <!-- 步骤2: 个人资料 -->
        <div class="form-step" v-show="currentStep === 2">
          <div class="form-group">
            <label for="school">
              <svg class="input-icon" viewBox="0 0 24 24" fill="none">
                <path d="M12 3L1 9l4 2.18v6L12 21l7-3.82v-6l2-1.09V17h2V9L12 3zm6.82 6L12 12.72 5.18 9 12 5.28 18.82 9zM17 15.99l-5 2.73-5-2.73v-3.72L12 15l5-2.73v3.72z" fill="currentColor"/>
              </svg>
              学校
            </label>
            <div class="input-wrapper">
              <input 
                type="text" 
                id="school" 
                v-model="userData.school" 
                required 
                placeholder="请输入学校名称"
              >
            </div>
          </div>

          <div class="form-group">
            <label for="ageGroup">
              <svg class="input-icon" viewBox="0 0 24 24" fill="none">
                <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z" fill="currentColor"/>
              </svg>
              年龄阶段（可多选）
            </label>
            <div class="select-wrapper">
              <select 
                id="ageGroup" 
                v-model="userData.age_groups" 
                multiple
              >
                <option value="primary">6-8岁小学</option>
                <option value="junior_low">9-11岁初中低龄组</option>
                <option value="junior_high">12-14岁初中高龄组</option>
                <option value="senior">15-17岁高中</option>
              </select>
              <svg class="select-arrow" viewBox="0 0 24 24" fill="none">
                <path d="M7 10l5 5 5-5H7z" fill="currentColor"/>
              </svg>
            </div>
            <small style="margin-top: 4px; font-size: 12px; color: #9ca3af;">
              按 Ctrl（Windows）或 Command（Mac）可多选多个年级段
            </small>
          </div>

          <!-- 错误消息 -->
          <transition name="shake">
            <div class="error-message" v-if="error">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" fill="currentColor"/>
              </svg>
              {{ error }}
            </div>
          </transition>

          <!-- 按钮组 -->
          <div class="button-group">
            <button type="button" class="back-btn" @click="prevStep">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" fill="currentColor"/>
              </svg>
              上一步
            </button>
            <button type="submit" class="register-btn" :disabled="loading">
              <span class="btn-content" v-if="!loading">
                <svg viewBox="0 0 24 24" fill="none">
                  <path d="M15 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm-9-2V7H4v3H1v2h3v3h2v-3h3v-2H6zm9 4c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" fill="currentColor"/>
                </svg>
                完成注册
              </span>
              <span class="btn-loading" v-else>
                <svg class="spinner" viewBox="0 0 24 24">
                  <circle class="path" cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="3"/>
                </svg>
                注册中...
              </span>
            </button>
          </div>
        </div>

        <!-- 登录链接 -->
        <div class="login-link">
          <span>已有账号？</span>
          <router-link to="/login">立即登录</router-link>
        </div>
      </form>

      <!-- 底部装饰 -->
      <div class="card-footer">
        <div class="footer-decoration">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
      </div>
    </div>

    <!-- 版权信息 -->
    <div class="copyright">
      © 2025 餐饮推荐系统 · 智能营养管理平台
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const userData = ref({
  username: '',
  password: '',
  school: '',
  // 支持多选年龄段
  age_groups: [] as string[]
})

const loading = ref(false)
const error = ref('')
const showPassword = ref(false)
const currentStep = ref(1)

// 密码强度计算
const passwordStrength = computed(() => {
  const password = userData.value.password
  if (!password) return { width: '0%', class: '', text: '' }
  
  let strength = 0
  if (password.length >= 6) strength++
  if (password.length >= 10) strength++
  if (/[A-Z]/.test(password)) strength++
  if (/[0-9]/.test(password)) strength++
  if (/[^A-Za-z0-9]/.test(password)) strength++
  
  if (strength <= 2) return { width: '33%', class: 'weak', text: '弱' }
  if (strength <= 3) return { width: '66%', class: 'medium', text: '中' }
  return { width: '100%', class: 'strong', text: '强' }
})

// 是否可以进入下一步
const canProceed = computed(() => {
  return userData.value.username.length >= 3 && userData.value.password.length >= 6
})

// 下一步
const nextStep = () => {
  if (canProceed.value) {
    currentStep.value = 2
  }
}

// 上一步
const prevStep = () => {
  currentStep.value = 1
  error.value = ''
}

// 生成唯一用户ID (已废弃，由后端自动生成ID)
/* const generateUserId = () => {
  const date = new Date()
  const timestamp = date.toISOString().slice(0, 10).replace(/-/g, '') + '-' + 
                   date.toTimeString().slice(0, 8).replace(/:/g, '')
  const random = Math.floor(100000 + Math.random() * 900000)
  return `user-${timestamp}-${random}`
} */

const handleRegister = async () => {
  loading.value = true
  error.value = ''
  
  try {
    if (!userData.value.age_groups || userData.value.age_groups.length === 0) {
      error.value = '请至少选择一个年龄阶段'
      loading.value = false
      return
    }

    const registerData = {
      ...userData.value,
      // 后端目前使用单个 age_group 字段，这里用逗号拼接多个年龄段
      age_group: userData.value.age_groups.join(','),
      // user_id: generateUserId() // 不再需要前端生成 user_id
    }
    
    await authStore.register(registerData)
    router.push('/')
  } catch (err: any) {
    error.value = err.response?.data?.detail || '注册失败，请检查输入信息'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 容器 */
.register-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  position: relative;
  overflow: hidden;
}

/* 动态背景 */
.animated-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #764ba2 0%, #667eea 50%, #43e97b 100%);
  z-index: -2;
}

.floating-shapes {
  position: absolute;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.shape {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 20s infinite ease-in-out;
}

.shape-1 {
  width: 80px;
  height: 80px;
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}

.shape-2 {
  width: 120px;
  height: 120px;
  top: 70%;
  left: 80%;
  animation-delay: -5s;
}

.shape-3 {
  width: 60px;
  height: 60px;
  top: 40%;
  left: 70%;
  animation-delay: -10s;
}

.shape-4 {
  width: 100px;
  height: 100px;
  top: 80%;
  left: 20%;
  animation-delay: -15s;
}

.shape-5 {
  width: 150px;
  height: 150px;
  top: 20%;
  left: 85%;
  animation-delay: -7s;
}

.shape-6 {
  width: 90px;
  height: 90px;
  top: 60%;
  left: 5%;
  animation-delay: -12s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
    opacity: 0.6;
  }
  25% {
    transform: translateY(-20px) rotate(90deg);
    opacity: 0.8;
  }
  50% {
    transform: translateY(0) rotate(180deg);
    opacity: 0.6;
  }
  75% {
    transform: translateY(20px) rotate(270deg);
    opacity: 0.8;
  }
}

/* 注册卡片 */
.register-card {
  width: 100%;
  max-width: 440px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 24px;
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(255, 255, 255, 0.3);
  padding: 2.5rem;
  position: relative;
  overflow: hidden;
  animation: cardSlideUp 0.6s ease-out;
}

@keyframes cardSlideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.register-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #764ba2 0%, #667eea 50%, #43e97b 100%);
}

/* Logo区域 */
.logo-section {
  text-align: center;
  margin-bottom: 1.5rem;
}

.logo-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 0.75rem;
  animation: logoFloat 3s ease-in-out infinite;
}

.logo-icon svg {
  width: 100%;
  height: 100%;
  filter: drop-shadow(0 4px 8px rgba(102, 126, 234, 0.3));
}

@keyframes logoFloat {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}

.app-title {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.375rem;
  letter-spacing: -0.5px;
}

.app-subtitle {
  font-size: 0.85rem;
  color: #6b7280;
  margin: 0;
}

/* 步骤指示器 */
.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
  gap: 0;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.875rem;
  font-weight: 600;
  background: #e5e7eb;
  color: #9ca3af;
  transition: all 0.3s ease;
}

.step.active .step-number {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.step.completed .step-number {
  background: #10b981;
  color: white;
}

.step-label {
  font-size: 0.75rem;
  color: #9ca3af;
  transition: color 0.3s ease;
}

.step.active .step-label {
  color: #667eea;
  font-weight: 500;
}

.step-line {
  width: 60px;
  height: 2px;
  background: #e5e7eb;
  margin: 0 0.5rem;
  margin-bottom: 1.25rem;
  transition: background 0.3s ease;
}

.step-line.active {
  background: linear-gradient(90deg, #10b981 0%, #667eea 100%);
}

/* 表单样式 */
.register-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-step {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  animation: stepFadeIn 0.3s ease-out;
}

@keyframes stepFadeIn {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.input-icon {
  width: 16px;
  height: 16px;
  color: #9ca3af;
}

.input-wrapper,
.select-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-wrapper input,
.select-wrapper select {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 1rem;
  color: #1f2937;
  background: #f9fafb;
  transition: all 0.3s ease;
}

.input-wrapper input {
  padding-right: 3rem;
}

.select-wrapper select {
  appearance: none;
  padding-right: 2.5rem;
  cursor: pointer;
}

.select-arrow {
  position: absolute;
  right: 1rem;
  width: 20px;
  height: 20px;
  color: #9ca3af;
  pointer-events: none;
}

.input-wrapper input::placeholder {
  color: #9ca3af;
}

.input-wrapper input:focus,
.select-wrapper select:focus {
  border-color: #667eea;
  background: #fff;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
  outline: none;
}

.toggle-password {
  position: absolute;
  right: 0.75rem;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #9ca3af;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.toggle-password:hover {
  color: #667eea;
  background: rgba(102, 126, 234, 0.1);
}

.toggle-password svg {
  width: 20px;
  height: 20px;
}

/* 密码强度 */
.password-strength {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.25rem;
}

.strength-bar {
  flex: 1;
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: hidden;
}

.strength-level {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease, background 0.3s ease;
}

.strength-level.weak {
  background: #ef4444;
}

.strength-level.medium {
  background: #f59e0b;
}

.strength-level.strong {
  background: #10b981;
}

.strength-text {
  font-size: 0.75rem;
  font-weight: 500;
}

.strength-text.weak {
  color: #ef4444;
}

.strength-text.medium {
  color: #f59e0b;
}

.strength-text.strong {
  color: #10b981;
}

/* 错误消息 */
.error-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.875rem 1rem;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: 1px solid #fecaca;
  border-radius: 12px;
  color: #dc2626;
  font-size: 0.875rem;
  font-weight: 500;
}

.error-message svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.shake-enter-active {
  animation: shake 0.5s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
  20%, 40%, 60%, 80% { transform: translateX(5px); }
}

/* 按钮 */
.next-btn,
.back-btn,
.register-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  width: 100%;
  padding: 1rem;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.next-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 14px rgba(102, 126, 234, 0.4);
  margin-top: 0.5rem;
}

.next-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
}

.next-btn:disabled {
  background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%);
  cursor: not-allowed;
  box-shadow: none;
}

.next-btn svg {
  width: 20px;
  height: 20px;
}

.button-group {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
}

.back-btn {
  flex: 1;
  background: #f3f4f6;
  color: #4b5563;
}

.back-btn:hover {
  background: #e5e7eb;
}

.back-btn svg {
  width: 20px;
  height: 20px;
}

.register-btn {
  flex: 2;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 14px rgba(102, 126, 234, 0.4);
  position: relative;
  overflow: hidden;
}

.register-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.register-btn:hover:not(:disabled)::before {
  left: 100%;
}

.register-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
}

.register-btn:disabled {
  background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%);
  cursor: not-allowed;
  box-shadow: none;
}

.btn-content,
.btn-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-content svg,
.btn-loading svg {
  width: 20px;
  height: 20px;
}

.spinner {
  animation: spin 1s linear infinite;
}

.spinner .path {
  stroke-dasharray: 50;
  stroke-dashoffset: 20;
  animation: dash 1.5s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes dash {
  0% { stroke-dashoffset: 50; }
  50% { stroke-dashoffset: 0; }
  100% { stroke-dashoffset: -50; }
}

/* 登录链接 */
.login-link {
  text-align: center;
  margin-top: 1rem;
  font-size: 0.9rem;
  color: #6b7280;
}

.login-link a {
  color: #667eea;
  font-weight: 600;
  text-decoration: none;
  margin-left: 0.25rem;
  transition: all 0.2s ease;
}

.login-link a:hover {
  color: #764ba2;
  text-decoration: underline;
}

/* 卡片底部装饰 */
.card-footer {
  margin-top: 1.25rem;
}

.footer-decoration {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  opacity: 0.3;
}

.dot:nth-child(2) {
  opacity: 0.6;
}

.dot:nth-child(3) {
  opacity: 1;
}

/* 版权信息 */
.copyright {
  position: absolute;
  bottom: 1.5rem;
  text-align: center;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.8);
}

/* 响应式 */
@media (max-width: 480px) {
  .register-container {
    padding: 1rem;
  }

  .register-card {
    padding: 2rem 1.5rem;
    border-radius: 20px;
  }

  .logo-icon {
    width: 56px;
    height: 56px;
  }

  .app-title {
    font-size: 1.375rem;
  }

  .step-line {
    width: 40px;
  }

  .input-wrapper input,
  .select-wrapper select {
    padding: 0.75rem;
    font-size: 0.9rem;
  }

  .button-group {
    flex-direction: column;
  }

  .back-btn,
  .register-btn {
    flex: 1;
  }
}
</style>

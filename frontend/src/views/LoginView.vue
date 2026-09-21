<template>
  <div class="login-container">
    <!-- 动态背景 -->
    <div class="animated-bg">
      <div class="floating-shapes">
        <div class="shape shape-1"></div>
        <div class="shape shape-2"></div>
        <div class="shape shape-3"></div>
        <div class="shape shape-4"></div>
      </div>
    </div>

    <!-- 登录卡片 -->
    <div class="login-card">
      <!-- Logo 区域 -->
      <div class="logo-section">
        <div class="logo-icon">🍽️</div>
        <h1 class="app-title">餐饮推荐系统</h1>
        <p class="app-subtitle">智能营养配餐，健康饮食管理</p>
      </div>

      <!-- 登录表单 -->
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input 
            type="text" 
            id="username" 
            v-model="username" 
            required 
            placeholder="请输入用户名"
            autocomplete="username"
          >
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <div class="input-wrapper">
            <input 
              :type="showPassword ? 'text' : 'password'" 
              id="password" 
              v-model="password" 
              required 
              placeholder="请输入密码"
              autocomplete="current-password"
            >
            <button 
              type="button" 
              class="toggle-password" 
              @click="showPassword = !showPassword"
              tabindex="-1"
            >
              {{ showPassword ? '👁️' : '👁️‍🗨️' }}
            </button>
          </div>
        </div>

        <!-- 错误消息 -->
        <div class="error-message" v-if="error">
          ⚠️ {{ error }}
        </div>

        <!-- 登录按钮 -->
        <button type="submit" class="login-btn" :disabled="loading">
          {{ loading ? '登录中...' : '登 录' }}
        </button>

        <!-- 注册链接 -->
        <div class="register-link">
          <span>还没有账号？</span>
          <router-link to="/register">立即注册</router-link>
        </div>
      </form>
    </div>

    <!-- 版权信息 -->
    <div class="copyright">
      © 2025 餐饮推荐系统 · 智能营养管理平台
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const timeoutMs = 30000
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject({ code: 'ECONNABORTED' }), timeoutMs)
    })
    await Promise.race([authStore.login(username.value, password.value), timeoutPromise])
    router.push('/')
  } catch (err: any) {
    if (err?.code === 'ECONNABORTED' || !err?.response) {
      error.value = '连接后端超时或失败，请检查后端服务或API地址'
    } else {
      error.value = err.response?.data?.detail || '登录失败，请检查用户名和密码'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 容器 */
.login-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
}

/* 动态背景 */
.animated-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  pointer-events: none;
}

.floating-shapes {
  position: relative;
  width: 100%;
  height: 100%;
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

/* 登录卡片 */
.login-card {
  width: 100%;
  max-width: 420px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  padding: 3rem;
  position: relative;
  z-index: 1;
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

.login-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  border-radius: 24px 24px 0 0;
}

/* Logo区域 */
.logo-section {
  text-align: center;
  margin-bottom: 2rem;
}

.logo-icon {
  font-size: 48px;
  margin-bottom: 1rem;
  animation: logoFloat 3s ease-in-out infinite;
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
  font-size: 1.75rem;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.5rem;
}

.app-subtitle {
  font-size: 0.9rem;
  color: #6b7280;
  margin: 0;
}

/* 表单样式 */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.form-group input {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 1rem;
  color: #1f2937;
  background: #f9fafb;
  transition: all 0.3s ease;
}

.form-group input::placeholder {
  color: #9ca3af;
}

.form-group input:focus {
  border-color: #667eea;
  background: #fff;
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
  outline: none;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-wrapper input {
  padding-right: 3rem;
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
  font-size: 16px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.toggle-password:hover {
  background: rgba(102, 126, 234, 0.1);
}

/* 错误消息 */
.error-message {
  padding: 0.875rem 1rem;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: 1px solid #fecaca;
  border-radius: 12px;
  color: #dc2626;
  font-size: 0.875rem;
  font-weight: 500;
}

/* 登录按钮 */
.login-btn {
  width: 100%;
  padding: 1rem;
  margin-top: 0.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 14px rgba(102, 126, 234, 0.4);
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
}

.login-btn:disabled {
  background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%);
  cursor: not-allowed;
  box-shadow: none;
}

/* 注册链接 */
.register-link {
  text-align: center;
  margin-top: 0.5rem;
  font-size: 0.9rem;
  color: #6b7280;
}

.register-link a {
  color: #667eea;
  font-weight: 600;
  text-decoration: none;
  margin-left: 0.25rem;
}

.register-link a:hover {
  color: #764ba2;
  text-decoration: underline;
}

/* 版权信息 */
.copyright {
  position: absolute;
  bottom: 1.5rem;
  text-align: center;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.8);
  z-index: 1;
}

/* 响应式 */
@media (max-width: 480px) {
  .login-container {
    padding: 1rem;
  }

  .login-card {
    padding: 2rem 1.5rem;
    border-radius: 20px;
  }

  .logo-icon {
    font-size: 40px;
  }

  .app-title {
    font-size: 1.5rem;
  }
}
</style>

<template>
  <div class="profile-container">
    <!-- 主要内容区域 -->
    <main class="main-content">
      <section class="profile-section">
        <h2>个人信息</h2>
        <div class="profile-card">
          <div class="profile-header">
            <div class="user-avatar-large">
              <img :src="userAvatar" alt="用户头像" class="avatar-img">

            </div>
            <div class="user-basic-info">
              <h3>{{ authStore.user?.username }}</h3>
              <p class="school">{{ authStore.user?.school }}</p>
              <p class="age-group">{{ ageGroupText[authStore.user?.age_group] }}</p>
            </div>
          </div>
          
          <div class="profile-body">
            <form @submit.prevent="handleUpdateProfile" class="profile-form">
              <div class="form-row">
                <div class="form-group">
                  <label for="username">用户名</label>
                  <input 
                    type="text" 
                    id="username" 
                    v-model="profileData.username" 
                    required 
                    placeholder="请输入用户名"
                  >
                </div>
                <div class="form-group">
                  <label for="school">学校</label>
                  <input 
                    type="text" 
                    id="school" 
                    v-model="profileData.school" 
                    required 
                    placeholder="请输入学校名称"
                  >
                </div>
              </div>
              
              <div class="form-row">
                <div class="form-group">
                  <label for="ageGroup">年龄阶段</label>
                  <select id="ageGroup" v-model="profileData.age_group" required>
                    <option value="">请选择年龄阶段</option>
                    <option value="小学">6-8岁小学</option>
                    <option value="初中低龄">9-11岁初中低龄组</option>
                    <option value="初中高龄">12-14岁初中高龄组</option>
                    <option value="高中">15-17岁高中</option>
                  </select>
                </div>
                <div class="form-group">
                  <label for="role">角色</label>
                  <input 
                    type="text" 
                    id="role" 
                    v-model="profileData.role" 
                    disabled
                  >
                  <small class="form-hint">角色不可修改</small>
                </div>
              </div>
              
              <div class="error-message" v-if="error">
                {{ error }}
              </div>
              
              <div class="form-actions">
                <button type="submit" class="save-btn" :disabled="loading">
                  {{ loading ? '保存中...' : '保存修改' }}
                </button>
                <button type="button" class="cancel-btn" @click="resetForm">
                  重置
                </button>
              </div>
            </form>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// 年龄阶段文本映射（包含旧的 key 与新的中文值以保持兼容）
const ageGroupText = {
  primary: '6-8岁小学',
  junior_low: '9-11岁初中低龄组',
  junior_high: '12-14岁初中高龄组',
  senior: '15-17岁高中',
  '小学': '6-8岁小学',
  '初中低龄': '9-11岁初中低龄组',
  '初中高龄': '12-14岁初中高龄组',
  '高中': '15-17岁高中'
}

// 个人信息数据
const profileData = ref({
  username: '',
  school: '',
  age_group: '',
  role: ''
})

const loading = ref(false)
const error = ref('')

// 头像相关
const userAvatar = ref('https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png')

// 初始化个人信息
const initProfile = () => {
  if (authStore.user) {
    profileData.value = {
      username: authStore.user.username,
      school: authStore.user.school,
      age_group: authStore.user.age_group,
      role: authStore.user.role || 'user'
    }
    
    if (authStore.user.avatar) {
      // 如果后端有头像，暂时忽略，统一使用默认头像
    }
  }
}

// 重置表单
const resetForm = () => {
  initProfile()
  error.value = ''
}

// 更新个人信息
const handleUpdateProfile = async () => {
  loading.value = true
  error.value = ''
  try {
    await authStore.updateProfile(profileData.value)
    router.go(0)
  } catch (err: any) {
    error.value = err.response?.data?.detail || '更新个人信息失败'
  } finally {
    loading.value = false
  }
}

// 组件挂载时初始化
onMounted(async () => {
  if (authStore.isLoggedIn && !authStore.user) {
    await authStore.fetchUser()
  }
  initProfile()
})
</script>

<style scoped>
.profile-container {
  width: 100%;
  margin: 0;
  padding: 0;
  font-family: Arial, sans-serif;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
}

/* 导航栏样式 */
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #4CAF50;
  color: white;
  padding: 1rem 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 100%;
  position: sticky;
  top: 0;
  z-index: 1000;
  margin: 0;
}

.navbar-left h1 {
  margin: 0;
  font-size: 1.5rem;
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.nav-links {
  display: flex;
  gap: 1.5rem;
}

.nav-link {
  color: white;
  text-decoration: none;
  font-size: 1rem;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.nav-link:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.nav-link.active {
  background-color: rgba(255, 255, 255, 0.3);
  font-weight: bold;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.username {
  font-weight: bold;
  font-size: 1.1rem;
}

.logout-btn {
  background-color: transparent;
  color: white;
  border: 1px solid white;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.logout-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

/* 主要内容区域 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 24px;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

/* 个人信息区域 */
.profile-section {
  background: #fff;
  padding: 24px;
  border-radius: 16px;
  box-shadow: 0 8px 20px rgba(0,0,0,0.06);
}

.profile-section h2 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 22px;
  font-weight: 600;
}

.profile-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.user-avatar-large {
  border-radius: 50%;
  overflow: hidden;
  width: 96px;
  height: 96px;
  border: 3px solid #409eff;
  position: relative;
  cursor: pointer;
  transition: transform 0.3s;
}

.user-avatar-large:hover {
  transform: scale(1.05);
}

.user-avatar-large .avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: opacity 0.3s;
}

.user-avatar-large:hover .avatar-img {
  opacity: 0.7;
}

.avatar-upload-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
  border-radius: 50%;
}

.user-avatar-large:hover .avatar-upload-overlay {
  opacity: 1;
}

.avatar-upload-icon {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: white;
  gap: 0.5rem;
}

.avatar-upload-icon svg {
  width: 24px;
  height: 24px;
}

.avatar-upload-icon span {
  font-size: 0.8rem;
  font-weight: 500;
}

/* 上传中状态 */
.user-avatar-large.uploading {
  opacity: 0.7;
  cursor: not-allowed;
}

.user-avatar-large.uploading:hover {
  transform: none;
}

.user-avatar-large.uploading .avatar-upload-overlay {
  opacity: 1;
  background-color: rgba(0, 0, 0, 0.7);
}

.user-avatar-large.uploading .avatar-upload-icon {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

.user-basic-info h3 {
  margin: 0 0 0.5rem 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.user-basic-info .school {
  margin: 0 0 0.5rem 0;
  color: #666;
  font-size: 14px;
}

.user-basic-info .age-group {
  margin: 0;
  color: #409eff;
  font-size: 14px;
  font-weight: 500;
}

/* 表单样式 */
.profile-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-row {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.form-group {
  flex: 1;
  min-width: 250px;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #303133;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.2);
}

.form-group input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.form-hint {
  display: block;
  margin-top: 0.25rem;
  color: #999;
  font-size: 0.8rem;
}

.error-message {
  color: #f44336;
  margin-bottom: 1rem;
  text-align: center;
  font-size: 0.9rem;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 12px;
}

.save-btn,
.cancel-btn {
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s, border-color 0.2s;
}

.save-btn {
  background-color: #409eff;
  color: white;
}

.save-btn:hover:not(:disabled) {
  background-color: #66b1ff;
}

.save-btn:disabled {
  background-color: #a0cfff;
  cursor: not-allowed;
}

.cancel-btn {
  background-color: #f5f7fa;
  color: #606266;
  border: 1px solid #ebeef5;
}

.cancel-btn:hover {
  background-color: #ebeef5;
  border-color: #dcdfe6;
  color: #303133;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .navbar {
    flex-direction: column;
    gap: 1rem;
  }
  
  .navbar-right {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
  }
  
  .nav-links {
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .profile-header {
    flex-direction: column;
    text-align: center;
  }
  
  .form-row {
    flex-direction: column;
  }
  
  .form-actions {
    flex-direction: column;
  }
}
</style>

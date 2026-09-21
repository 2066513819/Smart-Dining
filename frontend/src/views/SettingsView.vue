<template>
  <div class="settings-view">
    <el-card shadow="hover" class="page-card">
      <template #header>
        <div class="card-header">
          <span>账户设置</span>
        </div>
      </template>
      
      <el-tabs v-model="activeTab" class="settings-tabs">
        <!-- 基本信息设置 -->
        <el-tab-pane label="基本信息" name="basic">
          <el-form :model="basicForm" label-position="top" label-width="100px" class="settings-form">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="用户名">
                  <el-input v-model="basicForm.username" placeholder="请输入用户名" disabled />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="性别">
                  <el-select v-model="basicForm.gender" placeholder="请选择性别" style="width: 100%">
                    <el-option label="男" value="male" />
                    <el-option label="女" value="female" />
                    <el-option label="保密" value="secret" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="24">
                <el-form-item label="个人简介">
                  <el-input
                    v-model="basicForm.introduction"
                    type="textarea"
                    :rows="4"
                    placeholder="请输入个人简介"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            
            <div class="form-actions">
              <el-button type="primary" @click="saveBasicSettings">保存设置</el-button>
              <el-button @click="resetBasicForm">重置</el-button>
            </div>
          </el-form>
        </el-tab-pane>
        
        <!-- 安全设置 -->
        <el-tab-pane label="安全设置" name="security">
          <div class="security-section">
            <div class="security-item">
              <div class="security-item-info">
                <h4>修改密码</h4>
                <p>定期修改密码可以提高账户安全性</p>
              </div>
              <el-button type="primary" @click="$router.push('/change-password')">立即修改</el-button>
            </div>
          </div>
        </el-tab-pane>
        
        <!-- 通知设置 -->
        <el-tab-pane label="通知设置" name="notifications">
          <el-form :model="notificationForm" class="notification-form">
            <el-form-item label="新菜品推荐通知">
              <el-switch v-model="notificationForm.recommendation" />
            </el-form-item>
            
            <el-form-item label="系统消息通知">
              <el-switch v-model="notificationForm.system" />
            </el-form-item>
            
            <el-form-item label="活动通知">
              <el-switch v-model="notificationForm.activity" />
            </el-form-item>
            
            <div class="form-actions">
              <el-button type="primary" @click="saveNotificationSettings">保存设置</el-button>
              <el-button @click="resetNotificationForm">重置</el-button>
            </div>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

// 当前激活的标签页
const activeTab = ref('basic')

// 基本信息表单
const basicForm = reactive({
  username: 'admin',
  gender: 'male',
  introduction: '这是一个示例个人简介'
})

// 通知设置表单
const notificationForm = reactive({
  recommendation: true,
  system: true,
  activity: false
})

// 保存基本信息设置
const saveBasicSettings = () => {
  ElMessage.success('基本信息设置已保存')
}

// 重置基本信息表单
const resetBasicForm = () => {
  Object.assign(basicForm, {
    gender: 'male',
    introduction: '这是一个示例个人简介'
  })
}

// 保存通知设置
const saveNotificationSettings = () => {
  ElMessage.success('通知设置已保存')
}

// 重置通知设置
const resetNotificationForm = () => {
  Object.assign(notificationForm, {
    recommendation: true,
    system: true,
    activity: false
  })
}
</script>

<style scoped>
.settings-view {
  padding: 0;
  background-color: #f5f7fa;
  min-height: calc(100vh - 120px);
}

.page-card {
  margin-bottom: 20px;
}

.card-header {
  font-size: 20px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.settings-tabs {
  margin-top: 20px;
}

.settings-form {
  max-width: 800px;
  margin: 0 auto;
}

.security-section {
  padding: 20px 0;
}

.security-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background-color: #fafafa;
  border-radius: 8px;
  margin-bottom: 16px;
  border: 1px solid #e8e8e8;
  transition: all 0.3s ease;
}

.security-item:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border-color: #409eff;
}

.security-item-info h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 500;
}

.security-item-info p {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

.notification-form {
  max-width: 600px;
  margin: 0 auto;
}

.notification-form .el-form-item {
  margin-bottom: 24px;
}

.form-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 32px;
  padding-top: 20px;
  border-top: 1px solid #e8e8e8;
}
</style>
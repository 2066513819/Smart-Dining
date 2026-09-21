<template>
  <div class="change-password-view">
    <el-card shadow="hover" class="page-card">
      <template #header>
        <div class="card-header">
          <span>修改密码</span>
        </div>
      </template>
      
      <el-form 
        :model="passwordForm" 
        :rules="passwordRules" 
        ref="passwordFormRef"
        label-position="top" 
        label-width="100px" 
        class="password-form"
      >
        <div class="form-content">
          <el-form-item label="旧密码" prop="oldPassword">
            <el-input 
              v-model="passwordForm.oldPassword" 
              type="password" 
              placeholder="请输入旧密码"
              show-password
            />
          </el-form-item>
          
          <el-form-item label="新密码" prop="newPassword">
            <el-input 
              v-model="passwordForm.newPassword" 
              type="password" 
              placeholder="请输入新密码"
              show-password
              autocomplete="new-password"
            />
            <div class="password-tip">
              <el-tag type="info" size="small">密码要求：</el-tag>
              <span class="tip-text">8-20位，包含字母、数字和特殊字符</span>
            </div>
          </el-form-item>
          
          <el-form-item label="确认新密码" prop="confirmPassword">
            <el-input 
              v-model="passwordForm.confirmPassword" 
              type="password" 
              placeholder="请再次输入新密码"
              show-password
              autocomplete="new-password"
            />
          </el-form-item>
          
          <div class="form-actions">
            <el-button type="primary" @click="submitForm" :loading="submitting">确认修改</el-button>
            <el-button @click="resetForm">重置</el-button>
          </div>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

// 表单引用
const passwordFormRef = ref()

// 提交状态
const submitting = ref(false)

// 密码表单
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 密码表单验证规则
const passwordRules = {
  oldPassword: [
    { required: true, message: '请输入旧密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, max: 20, message: '密码长度在 8 到 20 个字符', trigger: 'blur' },
    { 
      pattern: /^(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]).*$/, 
      message: '密码必须包含字母、数字和特殊字符', 
      trigger: 'blur' 
    },
    { 
      validator: (rule: any, value: string, callback: any) => {
        if (value === passwordForm.oldPassword) {
          callback(new Error('新密码不能与旧密码相同'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { 
      validator: (rule: any, value: string, callback: any) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 提交表单
const submitForm = async () => {
  if (!passwordFormRef.value) return
  
  passwordFormRef.value.validate((valid: boolean) => {
    if (valid) {
      submitting.value = true
      
      // 模拟API请求延迟
      setTimeout(() => {
        submitting.value = false
        ElMessage.success('密码修改成功')
        resetForm()
      }, 1500)
    } else {
      return false
    }
  })
}

// 重置表单
const resetForm = () => {
  if (!passwordFormRef.value) return
  
  passwordFormRef.value.resetFields()
}
</script>

<style scoped>
.change-password-view {
  padding: 0;
  background-color: #f5f7fa;
  min-height: calc(100vh - 120px);
}

.page-card {
  margin-bottom: 20px;
  max-width: 600px;
  margin: 0 auto;
}

.card-header {
  font-size: 20px;
  font-weight: bold;
  display: flex;
  align-items: center;
}

.form-content {
  padding: 20px 0;
}

.password-form {
  max-width: 500px;
  margin: 0 auto;
}

.password-tip {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.tip-text {
  font-size: 12px;
  color: #909399;
}

.form-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 32px;
  padding-top: 20px;
  border-top: 1px solid #e8e8e8;
}

@media (max-width: 768px) {
  .password-form {
    padding: 0 16px;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .form-actions .el-button {
    width: 100%;
  }
}
</style>
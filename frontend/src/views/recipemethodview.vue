<template>
  <div class="recipe-method-container">
    <section class="header-section">
      <h2>菜谱制作方法</h2>
      <p>输入食材和菜名，智能生成详细的烹饪教程</p>
    </section>

    <div class="content-grid">
      <!-- 输入区域 -->
      <div class="input-card">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Edit /></el-icon>
              <span>烹饪需求输入</span>
            </div>
          </template>
          
          <el-form :model="form" label-position="top">
            <el-form-item label="菜品名称">
              <el-input 
                v-model="form.dishName" 
                placeholder="例如：红烧肉、宫保鸡丁..." 
                clearable
              />
            </el-form-item>
            
            <el-form-item label="已有食材">
              <el-input
                v-model="form.ingredients"
                type="textarea"
                :rows="4"
                placeholder="请输入您现有的食材，多个食材请用逗号或换行分隔..."
              />
            </el-form-item>

            <div class="action-buttons">
              <el-button 
                type="primary" 
                :loading="loading" 
                @click="generateRecipe"
                class="generate-btn"
              >
                <el-icon v-if="!loading"><MagicStick /></el-icon>
                立即生成制作教程
              </el-button>
              <el-button @click="resetForm">重置</el-button>
            </div>
          </el-form>
        </el-card>

        <div class="tips-card">
          <h4>💡 小贴士</h4>
          <ul>
            <li>输入越具体的食材，生成的步骤越精准。</li>
            <li>如果您有特殊的口味要求（如少油、少盐），也可以写在食材框中。</li>
            <li>生成的教程包含主料、辅料、调料及详细步骤。</li>
          </ul>
        </div>
      </div>

      <!-- 结果展示区域 -->
      <div class="result-card">
        <el-card shadow="hover" class="recipe-result-card">
          <template #header>
            <div class="card-header">
              <el-icon><Memo /></el-icon>
              <span>生成结果</span>
              <div v-if="recipeResult" class="header-actions">
                <el-button size="small" link @click="copyToClipboard">
                  <el-icon><CopyDocument /></el-icon>复制内容
                </el-button>
              </div>
            </div>
          </template>
          
          <div v-if="loading" class="loading-container">
            <el-skeleton :rows="10" animated />
            <p class="loading-text">智能体正在为您构思菜谱，请稍候...</p>
          </div>
          
          <div v-else-if="recipeResult" class="recipe-content">
            <div class="recipe-text">{{ recipeResult }}</div>
          </div>
          
          <el-empty v-else description="在左侧输入需求并点击生成，教程将在此处展示">
            <template #image>
              <div class="empty-icon">
                <el-icon :size="60"><Notebook /></el-icon>
              </div>
            </template>
          </el-empty>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Edit, MagicStick, Memo, CopyDocument, Notebook } from '@element-plus/icons-vue'
import axios from 'axios'

const form = reactive({
  dishName: '',
  ingredients: ''
})

const loading = ref(false)
const recipeResult = ref('')

const generateRecipe = async () => {
  if (!form.dishName && !form.ingredients) {
    ElMessage.warning('请至少输入菜品名称或食材')
    return
  }

  loading.value = true
  recipeResult.value = ''

  try {
    const query = `我想做这道菜：${form.dishName}。我现有的食材有：${form.ingredients}。请根据这些信息为我生成一份详细的烹饪制作教程，包括食材准备、步骤说明和烹饪小技巧。`
    
    const response = await axios.post('http://localhost/v1/chat-messages', {
      inputs: {},
      query: query,
      response_mode: 'blocking',
      user: 'user-' + Date.now(),
    }, {
      headers: {
        'Authorization': 'Bearer app-fXgp5Od3ZnuVXU5z9yYNogtJ',
        'Content-Type': 'application/json'
      }
    })

    if (response.data && response.data.answer) {
      recipeResult.value = response.data.answer
      ElMessage.success('生成成功！')
    } else {
      throw new Error('智能体响应异常')
    }
  } catch (error: any) {
    console.error('生成菜谱失败:', error)
    ElMessage.error(error.message || '生成失败，请检查智能体服务是否正常运行')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.dishName = ''
  form.ingredients = ''
  recipeResult.value = ''
}

const copyToClipboard = () => {
  navigator.clipboard.writeText(recipeResult.value).then(() => {
    ElMessage.success('已复制到剪贴板')
  })
}
</script>

<style scoped>
.recipe-method-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header-section {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 8px 20px rgba(0,0,0,0.06);
}

.header-section h2 {
  margin: 0 0 8px 0;
  color: #1f2f3d;
  font-size: 24px;
}

.header-section p {
  margin: 0;
  color: #909399;
}

.content-grid {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 24px;
}

@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

.input-card {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.generate-btn {
  width: 100%;
  margin-bottom: 12px;
  padding: 20px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.generate-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.action-buttons {
  margin-top: 10px;
}

.tips-card {
  background: #fdf6ec;
  border-radius: 12px;
  padding: 20px;
  border-left: 4px solid #e6a23c;
}

.tips-card h4 {
  margin: 0 0 12px 0;
  color: #e6a23c;
  display: flex;
  align-items: center;
  gap: 4px;
}

.tips-card ul {
  margin: 0;
  padding-left: 20px;
  color: #606266;
  font-size: 14px;
}

.tips-card li {
  margin-bottom: 8px;
}

.result-card {
  min-height: 600px;
}

.recipe-result-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.el-card__body) {
  flex: 1;
  overflow-y: auto;
}

.recipe-content {
  padding: 10px;
  line-height: 1.8;
}

.recipe-text {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  color: #303133;
}

.loading-container {
  padding: 20px;
  text-align: center;
}

.loading-text {
  margin-top: 20px;
  color: #909399;
  font-style: italic;
}

.empty-icon {
  color: #dcdfe6;
  margin-bottom: 10px;
}

.header-actions {
  margin-left: auto;
}

/* Markdown 样式微调 */
.markdown-body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  font-size: 16px;
}

:deep(.markdown-body h1), :deep(.markdown-body h2) {
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}
</style>

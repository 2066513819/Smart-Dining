<template>
  <div class="add-dish-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="title">添加新菜品</span>
          <el-button @click="$router.back()">返回</el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab" type="border-card">
        <!-- AI 生成页签 -->
        <el-tab-pane label="AI生成" name="ai">
          <div class="ai-section">
            <el-alert
              title="AI可以根据您的需求描述，自动生成菜品名称、配方及营养信息。"
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom: 20px"
            />
            
            <el-form label-position="top">
              <el-row :gutter="20">
                <el-col :span="4.8" style="width: 20%">
                  <el-form-item label="餐次类型">
                    <el-select v-model="aiOptions.meal_type" placeholder="请选择餐次" style="width: 100%">
                      <el-option label="不限" value="" />
                      <el-option label="早餐" value="早餐" />
                      <el-option label="午餐" value="午餐" />
                      <el-option label="晚餐" value="晚餐" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="4.8" style="width: 20%">
                  <el-form-item label="菜品类别">
                    <el-select v-model="aiOptions.category" placeholder="请选择类别" style="width: 100%">
                      <el-option label="不限" value="" />
                      <el-option
                        v-for="item in categoryOptions"
                        :key="item"
                        :label="item"
                        :value="item"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="4.8" style="width: 20%">
                  <el-form-item label="期望口味">
                    <el-input v-model="aiOptions.flavor" placeholder="如：清淡、麻辣" />
                  </el-form-item>
                </el-col>
                <el-col :span="4.8" style="width: 20%">
                  <el-form-item label="已有食材">
                    <el-input v-model="aiOptions.ingredients" placeholder="如：猪肉、粉丝" />
                  </el-form-item>
                </el-col>
                <el-col :span="4.8" style="width: 20%">
                  <el-form-item label="生成数量">
                    <el-input-number v-model="aiOptions.count" :min="1" :max="5" style="width: 100%" />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item label="需求描述">
                <el-input
                  v-model="aiPrompt"
                  type="textarea"
                  :rows="3"
                  placeholder="例如：推荐一道红烧排骨，要求营养均衡，并提供详细配料和克数。"
                />
              </el-form-item>
              <el-form-item>
                <div style="display: flex; align-items: center; gap: 16px; width: 100%;">
                  <el-button type="primary" :loading="aiLoading" @click="generateByAI">
                    开始生成
                  </el-button>
                  <div v-if="aiLoading" style="flex: 1;">
                    <el-progress 
                      :percentage="Math.round(loadingProgress)" 
                      :stroke-width="18" 
                      striped 
                      striped-flow 
                      :duration="10"
                      status="success"
                    />
                  </div>
                </div>
              </el-form-item>
            </el-form>

            <div v-if="generatedDishes.length > 0" class="generated-result">
              <el-divider>生成结果 ({{ generatedDishes.length }})</el-divider>
              
              <div v-for="(dish, index) in generatedDishes" :key="index" class="dish-item-card">
                <el-card shadow="hover" style="margin-bottom: 20px; border: 1px solid #e4e7ed;">
                  <template #header>
                    <div class="dish-card-header">
                      <span class="dish-num">菜品 {{ index + 1 }}</span>
                      <el-button type="danger" link @click="removeGeneratedDish(index)">删除此项</el-button>
                    </div>
                  </template>

                  <el-form :model="dish" label-position="top" class="edit-form">
                    <el-row :gutter="30">
                      <!-- 左侧：菜品配方框 -->
                      <el-col :span="14">
                        <div class="info-box recipe-box">
                          <div class="box-title">制作配方</div>
                          <el-form-item label="菜品名称">
                            <el-input v-model="dish.dish_name" placeholder="请输入菜品名称" />
                          </el-form-item>
                          <el-form-item label="制作配方">
                            <el-input v-model="dish.dish_recipe" type="textarea" :rows="10" placeholder="请输入食材及详细做法" />
                          </el-form-item>
                        </div>
                      </el-col>

                      <!-- 右侧：详细信息框 -->
                      <el-col :span="10">
                        <div class="info-box details-box">
                          <div class="box-title">详细参数</div>
                          
                          <el-row :gutter="10">
                            <el-col :span="12">
                              <el-form-item label="餐次类型">
                                <el-select v-model="dish.dish_type" placeholder="请选择" style="width: 100%">
                                  <el-option label="早餐" value="早餐" />
                                  <el-option label="午餐" value="午餐" />
                                  <el-option label="晚餐" value="晚餐" />
                                </el-select>
                              </el-form-item>
                            </el-col>
                            <el-col :span="12">
                              <el-form-item label="种类">
                                <el-select v-model="dish.category" placeholder="请选择种类" style="width: 100%">
                                  <el-option
                                    v-for="item in categoryOptions"
                                    :key="item"
                                    :label="item"
                                    :value="item"
                                  />
                                </el-select>
                              </el-form-item>
                            </el-col>
                          </el-row>
                          <el-row :gutter="10">
                            <el-col :span="12">
                              <el-form-item label="口味">
                                <el-input v-model="dish.flavor" placeholder="口味" />
                              </el-form-item>
                            </el-col>
                            <el-col :span="12">
                              <el-form-item label="适用时令">
                                <el-input v-model="dish.season" placeholder="如：四季" />
                              </el-form-item>
                            </el-col>
                          </el-row>

                          <div class="nutrition-grid">
                            <div class="nutrition-title">营养成分 (每100g)</div>
                            <el-row :gutter="15">
                              <el-col :span="12">
                                <el-form-item label="卡路里 (kcal)">
                                  <el-input-number v-model="dish.total_calories" :precision="1" :step="0.1" style="width: 100%" />
                                </el-form-item>
                              </el-col>
                              <el-col :span="12">
                                <el-form-item label="蛋白质 (g)">
                                  <el-input-number v-model="dish.total_protein" :precision="1" :step="0.1" style="width: 100%" />
                                </el-form-item>
                              </el-col>
                            </el-row>
                            <el-row :gutter="15">
                              <el-col :span="12">
                                <el-form-item label="脂肪 (g)">
                                  <el-input-number v-model="dish.total_fat" :precision="1" :step="0.1" style="width: 100%" />
                                </el-form-item>
                              </el-col>
                              <el-col :span="12">
                                <el-form-item label="碳水 (g)">
                                  <el-input-number v-model="dish.total_carbohydrates" :precision="1" :step="0.1" style="width: 100%" />
                                </el-form-item>
                              </el-col>
                            </el-row>
                          </div>
                        </div>
                      </el-col>
                    </el-row>
                  </el-form>
                </el-card>
              </div>

                <div class="form-actions" style="margin: 30px 0; text-align: center;">
                  <el-button type="success" size="large" @click="saveAllGeneratedDishes" :loading="saveLoading">
                    全部保存并入库
                  </el-button>
                  <el-button size="large" @click="generatedDishes = []">清空结果</el-button>
                </div>
              </div>
            </div>
          </el-tab-pane>

        <!-- 手动添加页签 -->
        <el-tab-pane label="手动添加" name="manual">
          <div class="manual-section">
            <el-form :model="manualDish" :rules="rules" ref="manualFormRef" label-width="100px">
              <el-form-item label="菜品名称" prop="dish_name">
                <el-input v-model="manualDish.dish_name" placeholder="请输入菜品名称" />
              </el-form-item>
              <el-form-item label="菜品配方" prop="dish_recipe">
                <el-input v-model="manualDish.dish_recipe" type="textarea" :rows="3" placeholder="请输入食材及做法" />
              </el-form-item>
              <el-form-item label="餐次类型" prop="dish_type">
                <el-select v-model="manualDish.dish_type" placeholder="请选择">
                  <el-option label="早餐" value="早餐" />
                  <el-option label="午餐" value="午餐" />
                  <el-option label="晚餐" value="晚餐" />
                </el-select>
              </el-form-item>
              <el-form-item label="种类">
                <el-select v-model="manualDish.category" placeholder="请选择种类" style="width: 100%">
                  <el-option
                    v-for="item in categoryOptions"
                    :key="item"
                    :label="item"
                    :value="item"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="口味">
                <el-input v-model="manualDish.flavor" placeholder="如：清淡、麻辣" />
              </el-form-item>
              <el-form-item label="时令">
                <el-input v-model="manualDish.season" placeholder="如：四季、夏季" />
              </el-form-item>
              
              <el-divider content-position="left">营养信息 (可选)</el-divider>
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="卡路里">
                    <el-input-number v-model="manualDish.total_calories" :precision="1" :step="0.1" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="蛋白质">
                    <el-input-number v-model="manualDish.total_protein" :precision="1" :step="0.1" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="脂肪">
                    <el-input-number v-model="manualDish.total_fat" :precision="1" :step="0.1" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="碳水">
                    <el-input-number v-model="manualDish.total_carbohydrates" :precision="1" :step="0.1" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="钙">
                    <el-input-number v-model="manualDish.total_calcium" :precision="1" :step="0.1" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="铁">
                    <el-input-number v-model="manualDish.total_iron" :precision="1" :step="0.1" />
                  </el-form-item>
                </el-col>
              </el-row>

              <div class="form-actions" style="margin-top: 30px; text-align: center;">
                <el-button type="primary" size="large" @click="saveManualDish" :loading="saveLoading">
                  提交添加
                </el-button>
                <el-button size="large" @click="resetManualForm">重置</el-button>
              </div>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useRecommendationStore, useAuthStore } from '../stores/auth'
import { dishTypeToBackend } from '../utils/constants'

const router = useRouter()
const recommendationStore = useRecommendationStore()
const authStore = useAuthStore()

// 种类选项
const categoryOptions = [
  '荤菜类',
  '主食类',
  '素菜类',
  '豆制品类',
  '奶及奶制品类',
  '水果类',
  '饮料类',
  '调味料类'
]

const activeTab = ref('ai')
const aiLoading = ref(false)
const saveLoading = ref(false)
const aiPrompt = ref('')
const aiOptions = reactive({
  meal_type: '',
  category: '',
  flavor: '',
  ingredients: '',
  count: 1
})
const generatedDishes = ref<any[]>([])

// 加载进度相关
const loadingProgress = ref(0)
let loadingTimer: any = null

const startLoadingProgress = () => {
  loadingProgress.value = 0
  if (loadingTimer) clearInterval(loadingTimer)
  loadingTimer = setInterval(() => {
    if (loadingProgress.value < 90) {
      const step = Math.max(1, (90 - loadingProgress.value) / 10)
      loadingProgress.value += step
    } else if (loadingProgress.value < 98) {
      loadingProgress.value += 0.5
    }
  }, 200)
}

const stopLoadingProgress = () => {
  if (loadingTimer) {
    clearInterval(loadingTimer)
    loadingTimer = null
  }
  loadingProgress.value = 100
  setTimeout(() => {
    if (!aiLoading.value) {
      loadingProgress.value = 0
    }
  }, 500)
}

const manualFormRef = ref()
const manualDish = reactive({
  dish_name: '',
  dish_recipe: '',
  dish_type: '',
  category: '',
  flavor: '',
  season: '',
  total_calories: 0,
  total_protein: 0,
  total_fat: 0,
  total_carbohydrates: 0,
  total_calcium: 0,
  total_iron: 0,
  total_vitamin_c: 0,
  is_published: 1
})

const rules = {
  dish_name: [{ required: true, message: '请输入菜品名称', trigger: 'blur' }],
  dish_type: [{ required: true, message: '请选择餐次类型', trigger: 'change' }],
  dish_recipe: [{ required: true, message: '请输入菜品配方', trigger: 'blur' }]
}

// AI 生成逻辑
const generateByAI = async () => {
  aiLoading.value = true
  startLoadingProgress()
  try {
    const userId = authStore.user?.id?.toString() || 'default_user'
    
    // 构建增强型提示词
    let fullPrompt = aiPrompt.value.trim() || '推荐一些健康美味的菜品'
    const rules = []
    if (aiOptions.meal_type) rules.push(`餐次类型：${aiOptions.meal_type}`)
    if (aiOptions.category) rules.push(`菜品类别：${aiOptions.category}`)
    if (aiOptions.flavor) rules.push(`期望口味：${aiOptions.flavor}`)
    if (aiOptions.ingredients) rules.push(`已有食材：${aiOptions.ingredients}`)
    rules.push(`生成菜品数量：${aiOptions.count}个`)
    
    if (rules.length > 0) {
      const categoryConstraint = aiOptions.category 
        ? `特别注意：所有生成的菜品的“种类”字段必须严格等于“${aiOptions.category}”。` 
        : `其中种类请从以下列表中选择一个最合适的：${categoryOptions.join('、')}。`
      
      fullPrompt = `【规则要求】\n${rules.join('\n')}\n\n【具体需求描述】\n${fullPrompt}\n\n请严格遵守规则要求进行推荐。如果生成多个菜品，请用“---”作为菜品之间的分隔符。每个菜品必须包含“名称、种类、配方、卡路里、蛋白质、脂肪、碳水化合物”字段。${categoryConstraint}`
    }

    const response = await recommendationStore.getRecommendationByPrompt(fullPrompt, userId)
    
    // 检查返回结果中是否包含错误信息
    if (response.error || (response.content && response.content.includes('获取推荐失败'))) {
      const errorMsg = response.content || 'AI服务暂时不可用'
      ElMessage.error(errorMsg)
      aiLoading.value = false
      stopLoadingProgress()
      return
    }

    const content = response.content || response.outputs?.text || ''
    
    // 按分隔符拆分多个菜品
    const dishTexts = content.split(/---|===/).filter(t => t.trim().length > 10)
    
    generatedDishes.value = dishTexts.map(text => {
      const nameMatch = text.match(/名称[：: ]*(.+)/)
      const categoryMatch = text.match(/种类[：: ]*(.+)/)
      const recipeMatch = text.match(/配方[：: ]*([\s\S]+?)(?=\n营养|\n口味|\n卡路里|$)/)
      const caloriesMatch = text.match(/卡路里[：: ]*(\d+\.?\d*)/)
      const proteinMatch = text.match(/蛋白质[：: ]*(\d+\.?\d*)/)
      const fatMatch = text.match(/脂肪[：: ]*(\d+\.?\d*)/)
      const carbsMatch = text.match(/碳水[：: ]*(\d+\.?\d*)/)

      // 优先使用 AI 生成的种类，但如果用户在规则中指定了种类，且 AI 生成的种类不在有效选项中或与用户指定不符，则强制纠正
      let finalCategory = categoryMatch ? categoryMatch[1].trim() : (aiOptions.category || '荤菜类')
      if (aiOptions.category && finalCategory !== aiOptions.category) {
        finalCategory = aiOptions.category
      } else if (!categoryOptions.includes(finalCategory)) {
        finalCategory = aiOptions.category || '荤菜类'
      }

      return {
        dish_name: nameMatch ? nameMatch[1].trim() : '未命名菜品',
        category: finalCategory,
        dish_recipe: recipeMatch ? recipeMatch[1].trim() : '未提供配方',
        total_calories: caloriesMatch ? parseFloat(caloriesMatch[1]) : 0,
        total_protein: proteinMatch ? parseFloat(proteinMatch[1]) : 0,
        total_fat: fatMatch ? parseFloat(fatMatch[1]) : 0,
        total_carbohydrates: carbsMatch ? parseFloat(carbsMatch[1]) : 0,
        dish_type: aiOptions.meal_type || '午餐',
        flavor: aiOptions.flavor || '原味',
        season: '四季皆宜',
        is_published: 1
      }
    })
    
    if (generatedDishes.value.length === 0) {
      ElMessage.warning('AI 未能生成有效的菜品建议，请尝试修改需求描述。')
    } else {
      ElMessage.success(`成功生成 ${generatedDishes.value.length} 个菜品建议`)
    }
  } catch (error: any) {
    console.error('AI 生成失败:', error)
    ElMessage.error('AI 服务请求出错')
  } finally {
    aiLoading.value = false
    stopLoadingProgress()
  }
}

// 删除某个生成的菜品
const removeGeneratedDish = (index: number) => {
  generatedDishes.value.splice(index, 1)
}

// 保存所有 AI 生成的菜品
const saveAllGeneratedDishes = async () => {
  if (generatedDishes.value.length === 0) return
  
  // 验证所有菜品名称不为空
  const invalidDish = generatedDishes.value.find(d => !d.dish_name || d.dish_name === '未命名菜品')
  if (invalidDish) {
    ElMessage.warning('请确保所有生成的菜品都有有效的名称')
    return
  }

  saveLoading.value = true
  let successCount = 0
  let failCount = 0
  let lastError = ''

  try {
    for (const dish of generatedDishes.value) {
      try {
        const payload = { 
          ...dish,
          dish_type: dishTypeToBackend(dish.dish_type)
        }
        await recommendationStore.createMenuItem(payload)
        successCount++
      } catch (error: any) {
        failCount++
        lastError = error.response?.data?.detail || error.message || '未知错误'
        console.error(`保存菜品 ${dish.dish_name} 失败:`, error)
      }
    }

    if (successCount > 0) {
      ElMessage.success(`成功保存 ${successCount} 个菜品到菜品库`)
      if (failCount === 0) {
        router.push('/dish-management')
      } else {
        ElMessage.warning(`${failCount} 个菜品保存失败: ${lastError}`)
        // 过滤掉已保存成功的
        // 这里简单处理，如果还有失败的就停留在页面
      }
    } else {
      ElMessage.error(`保存失败: ${lastError}`)
    }
  } finally {
    saveLoading.value = false
  }
}

// 保存手动添加的菜品
const saveManualDish = async () => {
  if (!manualFormRef.value) return
  
  await manualFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      saveLoading.value = true
      try {
        const payload = { 
          ...manualDish,
          dish_type: dishTypeToBackend(manualDish.dish_type)
        }
        await recommendationStore.createMenuItem(payload)
        ElMessage.success('菜品已成功添加到菜品库')
        router.push('/dish-management')
      } catch (error: any) {
        if (error.response?.status === 400) {
          ElMessage.error(error.response.data.detail || '菜品已存在')
        } else {
          ElMessage.error('添加失败: ' + (error.message || '未知错误'))
        }
      } finally {
        saveLoading.value = false
      }
    }
  })
}

const resetManualForm = () => {
  if (manualFormRef.value) {
    manualFormRef.value.resetFields()
  }
}
</script>

<style scoped>
.add-dish-container {
  max-width: 1100px;
  margin: 20px auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: bold;
}

.ai-section, .manual-section {
  padding: 10px;
}

.generated-result {
  margin-top: 20px;
  padding: 20px;
  background-color: #f8fafc;
  border-radius: 8px;
}

.edit-form {
  margin: 0;
}

.info-box {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  height: 100%;
  transition: all 0.3s ease;
}

.info-box:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.box-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #f1f5f9;
  display: flex;
  align-items: center;
}

.box-title::before {
  content: '';
  width: 4px;
  height: 16px;
  background: #409eff;
  margin-right: 8px;
  border-radius: 2px;
}

.nutrition-grid {
  margin-top: 20px;
  padding: 12px;
  background: #f1f5f9;
  border-radius: 6px;
}

.nutrition-title {
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 12px;
  text-align: center;
}

.dish-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dish-num {
  font-weight: bold;
  color: #409eff;
}

.generated-result {
  margin-top: 30px;
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.el-divider__text {
  background-color: #f8fafc;
}
</style>

<template>
  <div class="history-plans">
    <div class="header">
      <div>
        <h2>历史菜谱计划</h2>
        <p>查看并检索所有已发布的历史菜谱计划</p>
      </div>
      <div class="header-actions">
        <el-button @click="fetchPlans" :loading="loading">刷新</el-button>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="计划名称">
          <el-input v-model="filters.name" placeholder="搜索名称" clearable @input="debouncedFetch" />
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            @change="fetchPlans"
          />
        </el-form-item>
        <el-form-item label="年龄段">
          <el-select v-model="filters.age_group" placeholder="全部" clearable @change="fetchPlans">
            <el-option label="小学 (primary)" value="primary" />
            <el-option label="初中低龄 (junior_low)" value="junior_low" />
            <el-option label="初中高龄 (junior_high)" value="junior_high" />
            <el-option label="高中 (senior)" value="senior" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchPlans">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 列表展示 -->
    <div class="plans-list" v-loading="loading">
      <el-empty v-if="plans.length === 0 && !loading" description="未找到匹配的历史计划" />
      
      <div v-else class="plan-cards">
        <el-card v-for="plan in plans" :key="plan.id" class="plan-card" shadow="hover">
          <div class="plan-card-header">
            <div class="title-area">
              <span class="plan-title">{{ plan.name }}</span>
              <div class="tag-row" style="display: flex; gap: 8px; margin-top: 4px; align-items: center;">
                <el-tag size="small" type="primary" v-if="authStore.user?.role === 'admin'">{{ plan.school_name || '未知学校' }}</el-tag>
                <el-tag size="small" type="info" class="age-tag">{{ plan.age_group }}</el-tag>
                <el-tag size="small" type="warning" v-if="plan.total_cost">¥{{ plan.total_cost }}</el-tag>
                <el-tag 
                  size="small" 
                  :type="plan.delivery_status === 1 ? 'success' : 'info'"
                >
                  {{ plan.delivery_status === 1 ? '已配送' : '未配送' }}
                </el-tag>
              </div>
            </div>
            <span class="publish-date">发布于：{{ formatDateTime(plan.published_at) }}</span>
          </div>
          <div class="plan-preview">
            <span class="plan-date-info">应用日期：{{ plan.date }}</span>
            <span class="dish-count">包含 {{ plan.meals?.length || 0 }} 项安排</span>
          </div>
          <div class="plan-card-actions">
            <el-button 
              v-if="authStore.user?.role === 'admin'"
              plain
              class="plan-btn plan-btn-procurement"
              size="small" 
              @click.stop="viewProcurement(plan)"
            >
              采购需求
            </el-button>
            <el-button 
              v-if="authStore.user?.role === 'admin'"
              plain
              class="plan-btn"
              :class="plan.delivery_status === 1 ? 'plan-btn-undeliver' : 'plan-btn-deliver'"
              size="small" 
              @click.stop="toggleDeliveryStatus(plan)"
            >
              {{ plan.delivery_status === 1 ? '设为未配送' : '设为已配送' }}
            </el-button>
            <el-button plain class="plan-btn plan-btn-detail" size="small" @click="viewDetails(plan)">详情</el-button>
            <el-button plain class="plan-btn plan-btn-delete" size="small" @click.stop="deletePlan(plan)">删除</el-button>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 采购需求对话框 -->
    <el-dialog
      v-model="procurementDialogVisible"
      title="采购需求详情"
      width="600px"
    >
      <div v-if="selectedPlanForProcurement">
        <div style="margin-bottom: 16px;">
          <span style="font-weight: bold;">计划名称：</span>{{ selectedPlanForProcurement.name }}
          <el-tag size="small" style="margin-left: 8px;">{{ selectedPlanForProcurement.school_name || '未知学校' }}</el-tag>
        </div>
        <el-table :data="currentProcurementRows" stripe border style="width: 100%" height="400">
          <el-table-column prop="ingredient" label="食材名称" min-width="180" />
          <el-table-column prop="total_grams" label="总采购量(g)" width="150">
            <template #default="scope">{{ Number(scope.row.total_grams || 0).toFixed(1) }}</template>
          </el-table-column>
        </el-table>
        <div style="margin-top: 16px; text-align: right;">
           <el-button type="primary" @click="exportProcurementCSV">导出 CSV</el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailsVisible"
      :title="selectedPlan?.name"
      width="90%"
      top="5vh"
      custom-class="plan-details-dialog"
    >
      <div v-if="selectedPlan" class="details-content">
        <div class="details-meta">
          <el-descriptions :column="4" border>
            <el-descriptions-item label="计划日期">{{ selectedPlan.date }}</el-descriptions-item>
            <el-descriptions-item label="适用年龄">{{ selectedPlan.age_group }}</el-descriptions-item>
            <el-descriptions-item label="计划总成本">
              <span style="color: #f56c6c; font-weight: bold;">¥{{ selectedPlan.total_cost || 0 }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="早餐平均成本">
              <span style="color: #409eff; font-weight: bold;">¥{{ selectedPlan.breakfast_avg_cost || 0 }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="中餐平均成本">
              <span style="color: #67c23a; font-weight: bold;">¥{{ selectedPlan.lunch_avg_cost || 0 }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="晚餐平均成本">
              <span style="color: #e6a23c; font-weight: bold;">¥{{ selectedPlan.dinner_avg_cost || 0 }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="发布时间">{{ formatDateTime(selectedPlan.published_at) }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <el-table
          :data="groupedRows"
          stripe
          border
          style="width: 100%; margin-top: 20px;"
          class="csv-style-table"
        >
          <el-table-column prop="day" label="时间" width="120">
            <template #default="scope">
              <div class="day-cell">
                <div class="day-cell-title">第{{ scope.row.day }}天</div>
                <div v-if="scope.row.apply_date" class="day-cell-date">{{ scope.row.apply_date }}</div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="早餐" min-width="300">
            <template #default="scope">
              <div v-if="scope.row.breakfast?.length" class="meal-cell-container">
                <table class="meal-dish-table">
                  <tbody>
                    <tr v-for="dish in scope.row.breakfast" :key="dish.id">
                      <td class="category-td">
                        <el-tag size="small" type="success" effect="light" v-if="dish.dish_type">{{ dishTypeToText(dish.dish_type) }}</el-tag>
                        <el-tag size="small" type="info" effect="light" v-else-if="dish.meal_type">{{ dish.meal_type }}</el-tag>
                      </td>
                      <td class="name-td">
                        <el-tooltip :content="dish.dish_recipe" placement="top" :disabled="!dish.dish_recipe">
                          <span class="dish-name">{{ dish.dish_name }}</span>
                        </el-tooltip>
                        <span v-if="dish.cost_price" class="dish-cost" style="font-size: 11px; color: #909399; margin-left: 4px;">(¥{{ dish.cost_price }})</span>
                      </td>
                      <td class="nutrition-td">{{ dish.nutrition }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <span v-else class="no-meal">-</span>
            </template>
          </el-table-column>

          <el-table-column label="午餐" min-width="300">
            <template #default="scope">
              <div v-if="scope.row.lunch?.length" class="meal-cell-container">
                <table class="meal-dish-table">
                  <tbody>
                    <tr v-for="dish in scope.row.lunch" :key="dish.id">
                      <td class="category-td">
                        <el-tag size="small" type="success" effect="light" v-if="dish.dish_type">{{ dishTypeToText(dish.dish_type) }}</el-tag>
                        <el-tag size="small" type="info" effect="light" v-else-if="dish.meal_type">{{ dish.meal_type }}</el-tag>
                      </td>
                      <td class="name-td">
                        <el-tooltip :content="dish.dish_recipe" placement="top" :disabled="!dish.dish_recipe">
                          <span class="dish-name">{{ dish.dish_name }}</span>
                        </el-tooltip>
                        <span v-if="dish.cost_price" class="dish-cost" style="font-size: 11px; color: #909399; margin-left: 4px;">(¥{{ dish.cost_price }})</span>
                      </td>
                      <td class="nutrition-td">{{ dish.nutrition }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <span v-else class="no-meal">-</span>
            </template>
          </el-table-column>

          <el-table-column label="晚餐" min-width="300">
            <template #default="scope">
              <div v-if="scope.row.dinner?.length" class="meal-cell-container">
                <table class="meal-dish-table">
                  <tbody>
                    <tr v-for="dish in scope.row.dinner" :key="dish.id">
                      <td class="category-td">
                        <el-tag size="small" type="success" effect="light" v-if="dish.dish_type">{{ dishTypeToText(dish.dish_type) }}</el-tag>
                        <el-tag size="small" type="info" effect="light" v-else-if="dish.meal_type">{{ dish.meal_type }}</el-tag>
                      </td>
                      <td class="name-td">
                        <el-tooltip :content="dish.dish_recipe" placement="top" :disabled="!dish.dish_recipe">
                          <span class="dish-name">{{ dish.dish_name }}</span>
                        </el-tooltip>
                      </td>
                      <td class="nutrition-td">{{ dish.nutrition }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <span v-else class="no-meal">-</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useAuthStore, useRecommendationStore } from '../stores/auth'
import { ElMessage } from 'element-plus'
import { dishTypeToText } from '../utils/constants'

const authStore = useAuthStore()
const recStore = useRecommendationStore()
const loading = ref(false)
const plans = ref<any[]>([])
const detailsVisible = ref(false)
const selectedPlan = ref<any>(null)

const filters = reactive({
  name: '',
  dateRange: [] as string[],
  age_group: ''
})

const fetchPlans = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (filters.name) params.name = filters.name
    if (filters.age_group) params.age_group = filters.age_group
    if (filters.dateRange && filters.dateRange.length === 2) {
      params.start_date = filters.dateRange[0]
      params.end_date = filters.dateRange[1]
    }

    // 修正路径：从 /meal-plans/published 改为 /meal_plans/published
    const res = await recStore.api.get('/meal_plans/published', { params })
    plans.value = res
  } catch (error: any) {
    ElMessage.error('加载历史计划失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

let timer: any = null
const debouncedFetch = () => {
  if (timer) clearTimeout(timer)
  timer = setTimeout(fetchPlans, 500)
}

const resetFilters = () => {
  filters.name = ''
  filters.dateRange = []
  filters.age_group = ''
  fetchPlans()
}

const viewDetails = (plan: any) => {
  selectedPlan.value = plan
  detailsVisible.value = true
}

const toggleDeliveryStatus = async (plan: any) => {
  try {
    const newStatus = plan.delivery_status === 1 ? 0 : 1
    await recStore.api.put(`/meal_plans/${plan.id}/delivery-status`, { status: newStatus })
    plan.delivery_status = newStatus
    ElMessage.success('状态已更新')
  } catch (error: any) {
    ElMessage.error('更新配送状态失败')
    console.error(error)
  }
}

// 采购需求相关逻辑
const procurementDialogVisible = ref(false)
const selectedPlanForProcurement = ref<any>(null)
const currentProcurementRows = ref<any[]>([])

const viewProcurement = (plan: any) => {
  selectedPlanForProcurement.value = plan
  
  // 解析 meals 字段获取采购信息
  const meals = Array.isArray(plan.meals) ? plan.meals : (typeof plan.meals === 'string' ? JSON.parse(plan.meals || '[]') : [])
  const row = meals.find((m: any) => m && typeof m === 'object' && String(m.meal_type || '').toLowerCase() === '__procurement__')
  const rows = row?.procurement_rows || []
  
  currentProcurementRows.value = Array.isArray(rows) 
    ? rows.map((r: any) => ({ ingredient: String(r?.ingredient || '').trim(), total_grams: Number(r?.total_grams) || 0 }))
          .filter((r: any) => r.ingredient)
    : []
    
  if (currentProcurementRows.value.length === 0) {
    ElMessage.info('该计划暂无采购数据')
    return
  }
  
  procurementDialogVisible.value = true
}

const exportProcurementCSV = () => {
  const rows = currentProcurementRows.value
  if (!rows || rows.length === 0) {
    ElMessage.warning('当前采购表为空')
    return
  }

  const header = ['食材', '总采购量(g)']
  const lines = [header.join(',')]
  for (const r of rows) {
    lines.push(`"${r.ingredient}",${r.total_grams}`)
  }
  const csvContent = '\uFEFF' + lines.join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', `采购表_${selectedPlanForProcurement.value?.name || 'export'}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const deletePlan = async (plan: any) => {
  try {
    await recStore.api.delete(`/meal_plans/${plan.id}`)
    ElMessage.success('已删除')
    fetchPlans()
  } catch (error: any) {
    ElMessage.error('删除失败')
    console.error(error)
  }
}

const formatDateTime = (isoStr: string) => {
  if (!isoStr) return '-'
  try {
    const d = new Date(isoStr)
    if (isNaN(d.getTime())) return isoStr
    
    // 使用中国时区进行格式化
    const year = d.toLocaleDateString('zh-CN', { timeZone: 'Asia/Shanghai', year: 'numeric' }).replace(/年|/g, '')
    const month = d.toLocaleDateString('zh-CN', { timeZone: 'Asia/Shanghai', month: '2-digit' }).replace(/月|/g, '')
    const day = d.toLocaleDateString('zh-CN', { timeZone: 'Asia/Shanghai', day: '2-digit' }).replace(/日|/g, '')
    const time = d.toLocaleTimeString('zh-CN', { timeZone: 'Asia/Shanghai', hour12: false, hour: '2-digit', minute: '2-digit' })
    
    // 简单的补齐逻辑，防止 toLocaleDateString 格式不统一
    const formatPart = (s: string) => s.padStart(2, '0').slice(-2)
    
    // 重新组合
    const y = d.getFullYear()
    const mo = String(d.getMonth() + 1).padStart(2, '0')
    const da = String(d.getDate()).padStart(2, '0')
    const ho = String(d.getHours()).padStart(2, '0')
    const mi = String(d.getMinutes()).padStart(2, '0')
    
    // 如果浏览器已经在 UTC+8 附近，直接用原逻辑即可
    // 如果不在，则使用 toLocaleString 确保显示的是北京时间
    return d.toLocaleString('zh-CN', { 
      timeZone: 'Asia/Shanghai',
      hour12: false,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }).replace(/\//g, '-')
  } catch (e) {
    return isoStr
  }
}

// 分组逻辑复用自 HomeView.vue
const groupedRows = computed(() => {
  if (!selectedPlan.value || !selectedPlan.value.meals) return []
  
  const map: Record<number, any> = {}
  for (const raw of selectedPlan.value.meals) {
    if (!raw || typeof raw !== 'object') continue
    if (String(raw.meal_type || '').toLowerCase() === '__procurement__') continue
    
    const day = Number(raw.day) || 1
    if (!map[day]) {
      map[day] = { day, apply_date: raw.apply_date || '', breakfast: [], lunch: [], dinner: [] }
    }
    
    const mt = normalizeMealType(raw.meal_type || raw.time)
    const item = {
      ...raw,
      dish_name: raw.name || raw.dish_name || '未知菜品',
      dish_recipe: raw.dish_recipe || raw.recipe || '',
      meal_type: mt,
      dish_type: raw.category || raw.dish_type || '',
      nutrition: raw.nutrition || ''
    }
    
    if (mt === '早餐') map[day].breakfast.push(item)
    else if (mt === '午餐') map[day].lunch.push(item)
    else if (mt === '晚餐') map[day].dinner.push(item)
  }
  
  return Object.values(map).sort((a: any, b: any) => a.day - b.day)
})

const normalizeMealType = (t: any) => {
  const s = String(t || '').toLowerCase()
  if (s.includes('break') || s.includes('早')) return '早餐'
  if (s.includes('lunch') || s.includes('中') || s.includes('午')) return '午餐'
  if (s.includes('dinner') || s.includes('晚')) return '晚餐'
  return t
}

onMounted(() => {
  fetchPlans()
})
</script>

<style scoped>
.history-plans {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header h2 {
  font-size: 24px;
  color: #1f2937;
  margin-bottom: 4px;
}

.header p {
  color: #6b7280;
  font-size: 14px;
}

.filter-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  margin-bottom: 24px;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 20px;
}

.plan-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.plan-card {
  border-radius: 12px;
  transition: all 0.3s;
}

.plan-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.title-area {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  flex: 1;
}

.plan-title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

.age-tag {
  width: fit-content;
}

.publish-date {
  font-size: 12px;
  color: #9ca3af;
  white-space: nowrap;
  flex-shrink: 0;
  padding-top: 2px;
}

.plan-preview {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: #4b5563;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
}

/* 底部一排操作按钮，避免挤在右侧一列 */
.plan-card-actions {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
}

.plan-card-actions :deep(.el-button) {
  margin-left: 0 !important;
  font-weight: 500;
}

/* 历史菜谱按钮：改为餐次管理同风格的浅色低饱和 */
.plan-card-actions :deep(.plan-btn) {
  border-radius: 6px;
}

.plan-card-actions :deep(.plan-btn-procurement) {
  background-color: #f4f7fb !important;
  border-color: #dce4ee !important;
  color: #5a7a9e !important;
}
.plan-card-actions :deep(.plan-btn-procurement:hover),
.plan-card-actions :deep(.plan-btn-procurement:focus) {
  background-color: #e8eef6 !important;
  border-color: #c9d6e8 !important;
  color: #4a6585 !important;
}

.plan-card-actions :deep(.plan-btn-deliver) {
  background-color: #f0f8f4 !important;
  border-color: #d8ebe1 !important;
  color: #5f8f75 !important;
}
.plan-card-actions :deep(.plan-btn-deliver:hover),
.plan-card-actions :deep(.plan-btn-deliver:focus) {
  background-color: #e5f3eb !important;
  border-color: #cde5d8 !important;
  color: #4f7b65 !important;
}

.plan-card-actions :deep(.plan-btn-undeliver) {
  background-color: #faf6f0 !important;
  border-color: #e8e0d6 !important;
  color: #8b7355 !important;
}
.plan-card-actions :deep(.plan-btn-undeliver:hover),
.plan-card-actions :deep(.plan-btn-undeliver:focus) {
  background-color: #f3ebe0 !important;
  border-color: #ddd2c4 !important;
  color: #6b5a45 !important;
}

.plan-card-actions :deep(.plan-btn-detail) {
  background-color: #f5f6f8 !important;
  border-color: #e2e4e8 !important;
  color: #6b7280 !important;
}
.plan-card-actions :deep(.plan-btn-detail:hover),
.plan-card-actions :deep(.plan-btn-detail:focus) {
  background-color: #ebecef !important;
  border-color: #d1d5db !important;
  color: #4b5563 !important;
}

.plan-card-actions :deep(.plan-btn-delete) {
  background-color: #fdf5f5 !important;
  border-color: #f0dede !important;
  color: #b87a7a !important;
}
.plan-card-actions :deep(.plan-btn-delete:hover),
.plan-card-actions :deep(.plan-btn-delete:focus) {
  background-color: #f8eaea !important;
  border-color: #e5cfcf !important;
  color: #9a6565 !important;
}

/* 复用 HomeView 的表格样式 */
.csv-style-table {
  border-radius: 8px;
  overflow: hidden;
}

.day-cell {
  text-align: center;
}

.day-cell-title {
  font-weight: bold;
  font-size: 16px;
  color: #374151;
}

.day-cell-date {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}

.meal-cell-container {
  padding: 4px 0;
}

.meal-dish-table {
  width: 100%;
  border-collapse: collapse;
}

.meal-dish-table td {
  padding: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.meal-dish-table tr:last-child td {
  border-bottom: none;
}

.category-td {
  width: 90px;
}

.name-td {
  font-weight: 500;
  color: #1f2937;
}

.nutrition-td {
  font-size: 12px;
  color: #6b7280;
  text-align: right;
}

.dish-name {
  cursor: help;
}

.no-meal {
  color: #d1d5db;
  font-style: italic;
}

.details-meta {
  margin-bottom: 20px;
}

:deep(.plan-details-dialog) {
  border-radius: 16px;
}

:deep(.plan-details-dialog .el-dialog__body) {
  padding: 10px 25px 30px;
}
</style>

<template>
  <div class="admin-container">
    <main class="main-content">
      <section class="header-section">
        <h2>管理员面板</h2>
        <p>管理用户、菜品与系统数据</p>
        <div class="current-user">
          <span>当前账户：{{ authStore.user?.username || '未登录' }}</span>
          <el-tag type="primary" style="margin-left:8px">{{ authStore.user?.role || 'user' }}</el-tag>
        </div>
      </section>
      
      <el-tabs v-model="activeTab" class="admin-tabs">
        <el-tab-pane label="用户管理" name="users">
          <div class="toolbar" style="justify-content: space-between;">
            <div style="display: flex; gap: 12px;">
              <el-input v-model="userKeyword" placeholder="搜索用户名或学校" clearable style="max-width: 300px" />
              <el-button type="primary" @click="loadUsers" :loading="loadingUsers">刷新</el-button>
            </div>
            <el-button type="success" @click="showAddUserDialog">新增账户</el-button>
          </div>
          
          <el-table v-if="filteredUsers.length > 0" :data="filteredUsers" stripe style="width: 100%">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="username" label="用户名" width="180" />
            <el-table-column prop="school" label="学校" width="220" />
            <el-table-column prop="age_group" label="年龄阶段" width="180" />
            <el-table-column prop="role" label="角色" width="120">
              <template #default="{ row }">
                <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">{{ row.role === 'admin' ? '管理员' : '普通用户' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="280">
              <template #default="{ row }">
                <el-button size="small" type="primary" @click="editUser(row)">编辑</el-button>
                <el-button 
                  size="small" 
                  type="danger" 
                  @click="deleteUser(row.id)" 
                >删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else :description="userEmptyDesc" />
        </el-tab-pane>

        <el-tab-pane label="发布计划" name="plans">
          <div class="toolbar" style="justify-content: space-between; flex-wrap: wrap;">
            <div style="display: flex; gap: 12px; flex-wrap: wrap; align-items: center;">
              <el-input v-model="planKeyword" placeholder="搜索计划名称" clearable style="width: 180px" />
              <el-select v-model="planFilterSchool" placeholder="选择学校" clearable style="width: 140px">
                <el-option v-for="school in planSchools" :key="school" :label="school" :value="school" />
              </el-select>
              <el-select v-model="planFilterAgeGroup" placeholder="年龄段" clearable style="width: 120px">
                <el-option label="小学" value="primary" />
                <el-option label="初中低龄" value="junior_low" />
                <el-option label="初中高龄" value="junior_high" />
                <el-option label="高中" value="senior" />
              </el-select>
              <el-date-picker
                v-model="planFilterDateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                style="width: 220px"
              />
              <el-button type="primary" @click="loadPlans" :loading="loadingPlans">刷新</el-button>
              <el-button @click="resetPlanFilters">重置</el-button>
            </div>
          </div>
          
          <el-table v-if="filteredPlans.length > 0" :data="filteredPlans" stripe style="width: 100%">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="计划名称" width="180" show-overflow-tooltip />
            <el-table-column prop="school_name" label="发布学校" width="140" show-overflow-tooltip />
            <el-table-column prop="date" label="应用日期" width="110" />
            <el-table-column prop="age_group" label="年龄段" width="90" />
            <el-table-column prop="delivery_status" label="已配送" width="80">
              <template #default="{ row }">
                <el-tag :type="row.delivery_status === 1 ? 'success' : 'info'" size="small">
                  {{ row.delivery_status === 1 ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="320" fixed="right">
              <template #default="{ row }">
                <div class="plan-actions-row">
                  <el-button
                    plain
                    class="plan-btn plan-btn-procurement"
                    size="small"
                    @click="viewProcurement(row)"
                  >
                    采购需求
                  </el-button>
                  <el-button
                    plain
                    class="plan-btn plan-btn-export"
                    size="small"
                    @click="exportPlanCSV(row)"
                  >
                    导出CSV
                  </el-button>
                  <el-button
                    plain
                    class="plan-btn"
                    :class="row.delivery_status === 1 ? 'plan-btn-undeliver' : 'plan-btn-deliver'"
                    size="small"
                    @click="toggleDeliveryStatus(row)"
                  >
                    {{ row.delivery_status === 1 ? '设为未配送' : '设为已配送' }}
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-else description="暂无发布计划" />
        </el-tab-pane>
        
        <el-tab-pane label="系统统计" name="stats">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">{{ users.length }}</div>
              <div class="stat-label">用户总数</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ totalDatabaseDishes }}</div>
              <div class="stat-label">数据库全部菜品</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ publishedMealPlansCount }}</div>
              <div class="stat-label">已发布菜谱计划</div>
            </div>
          </div>
          <div class="toolbar" style="margin-top:12px;">
            <span style="color:#666;">统计范围：</span>
            <el-radio-group v-model="statsRange">
              <el-radio-button :label="7">7天</el-radio-button>
              <el-radio-button :label="14">14天</el-radio-button>
              <el-radio-button :label="30">30天</el-radio-button>
            </el-radio-group>
          </div>
          <el-empty v-if="!statsDays.length" description="暂无统计数据，最近未新增菜品" />
          <div v-else class="charts-grid">
            <div class="chart-card">
              <div class="chart-title">近{{ statsDays.length }}天用户活跃量</div>
              <canvas ref="userChartRef" class="chart-canvas"></canvas>
            </div>
            <div class="chart-card">
              <div class="chart-title">近{{ statsDays.length }}天新增菜品数</div>
              <canvas ref="dishChartRef" class="chart-canvas"></canvas>
            </div>
          </div>
          <div v-if="showTooltip" class="chart-tooltip" :style="{ left: tooltipX + 'px', top: tooltipY + 'px' }">
            <div class="tooltip-title">{{ tooltipLabel }}</div>
            <div class="tooltip-value">{{ tooltipValue }}</div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="配餐规则" name="rules">
          <div class="toolbar" style="justify-content: space-between; align-items: center;">
            <div class="rule-title" style="font-size: 16px; font-weight: 600; color: #374151;">配餐规则与成本设置</div>
            <el-button type="primary" @click="applyMealRules" :loading="savingRules" size="large" style="padding: 0 32px;">应用配置</el-button>
          </div>

          <!-- 新增：餐饮形式设置 -->
          <el-card shadow="never" style="margin-bottom: 20px;">
            <template #header>
              <div style="display:flex;align-items:center;justify-content:space-between;">
                <span style="font-weight:600;">餐饮形式设置</span>
              </div>
            </template>
            <div style="padding: 10px 0;">
              <el-radio-group v-model="diningStyle" size="large">
                <el-radio-button label="团餐">
                  <div style="display:flex; flex-direction:column; align-items:center; padding: 10px 20px;">
                    <span style="font-size: 16px; font-weight: 600;">团餐</span>
                    <span style="font-size: 12px; color: #6b7280; margin-top: 4px;">品类丰富，自助配餐，营养计算不针对个人</span>
                  </div>
                </el-radio-button>
                <el-radio-button label="盘餐">
                  <div style="display:flex; flex-direction:column; align-items:center; padding: 10px 20px;">
                    <span style="font-size: 16px; font-weight: 600;">盘餐</span>
                    <span style="font-size: 12px; color: #6b7280; margin-top: 4px;">标准份量，内容统一，适合大规模供应</span>
                  </div>
                </el-radio-button>
              </el-radio-group>
            </div>
          </el-card>

          <!-- 新增：每餐成本设置 -->
          <el-card shadow="never" style="margin-bottom: 20px;">
            <template #header>
              <div style="display:flex;align-items:center;justify-content:space-between;">
                <span style="font-weight:600;">配餐基础参数设置</span>
                <span style="color:#6b7280;font-size:12px;">设置每一餐的基准成本（元）与默认人数</span>
              </div>
            </template>
            <div v-for="m in mealPanels" :key="'base-' + m.key" style="margin-bottom: 12px;">
              <el-row :gutter="20" align="middle">
                <el-col :span="4">
                  <span style="font-weight: 600; color: #374151;">{{ m.label }}</span>
                </el-col>
                <el-col :span="10">
                  <div style="display: flex; align-items: center; justify-content: space-between; background: #f9fafb; padding: 10px 16px; border-radius: 8px;">
                    <span style="color: #4b5563;">{{ m.label }}人数 (人)</span>
                    <el-input-number
                      v-model="mealPeople[m.key]"
                      :min="1"
                      :precision="0"
                      :step="1"
                      controls-position="right"
                      style="width: 140px;"
                    />
                  </div>
                </el-col>
                <el-col :span="10">
                  <div style="display: flex; align-items: center; justify-content: space-between; background: #f9fafb; padding: 10px 16px; border-radius: 8px;">
                    <span style="color: #4b5563;">{{ m.label }}平均成本 (元)</span>
                    <el-input-number
                      v-model="mealCosts[m.key]"
                      :min="0"
                      :precision="2"
                      :step="1"
                      controls-position="right"
                      style="width: 140px;"
                    />
                  </div>
                </el-col>
              </el-row>
            </div>
          </el-card>

          <el-row :gutter="16">
            <el-col :span="8" v-for="m in mealPanels" :key="m.key">
              <el-card shadow="never">
                <template #header>
                  <div style="display:flex;align-items:center;justify-content:space-between;">
                    <span style="font-weight:600;">{{ m.label }}</span>
                    <span style="color:#6b7280;font-size:12px;">选中类别并设置数量</span>
                  </div>
                </template>

                <el-table :data="mealRuleRows[m.key]" size="small" border>
                  <el-table-column prop="category" label="类别" min-width="120" />
                  <el-table-column label="选择" width="90">
                    <template #default="scope">
                      <el-switch v-model="scope.row.enabled" @change="onToggleRule(scope.row)" />
                    </template>
                  </el-table-column>
                  <el-table-column label="数量" width="120">
                    <template #default="scope">
                      <el-input-number
                        v-model="scope.row.count"
                        :min="1"
                        :max="20"
                        :disabled="!scope.row.enabled"
                        controls-position="right"
                        style="width:100%;"
                      />
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
            </el-col>
          </el-row>
        </el-tab-pane>
      </el-tabs>

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

      <!-- 用户编辑/新增对话框 -->
      <el-dialog
        v-model="userDialogVisible"
        :title="isEdit ? '编辑用户' : '新增用户'"
        width="500px"
      >
        <el-form :model="userForm" label-width="80px">
          <el-form-item label="用户名">
            <el-input v-model="userForm.username" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input 
              v-model="userForm.password" 
              type="password" 
              :placeholder="isEdit ? '留空表示不修改' : '请输入密码'" 
              show-password
            />
          </el-form-item>
          <el-form-item label="所属学校">
            <el-input v-model="userForm.school" placeholder="请输入学校名称" />
          </el-form-item>
          <el-form-item label="年龄阶段">
            <el-select v-model="userForm.age_group" placeholder="请选择年龄阶段" style="width: 100%">
              <el-option label="小学 (primary)" value="primary" />
              <el-option label="初中低龄 (junior_low)" value="junior_low" />
              <el-option label="初中高龄 (junior_high)" value="junior_high" />
              <el-option label="高中 (senior)" value="senior" />
            </el-select>
          </el-form-item>
          <el-form-item label="角色">
            <el-select v-model="userForm.role" placeholder="请选择角色" style="width: 100%">
              <el-option label="普通用户" value="user" />
              <el-option label="超级管理员" value="admin" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="userDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="saveUser" :loading="savingUser">确认</el-button>
          </span>
        </template>
      </el-dialog>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick, onBeforeUnmount, reactive } from 'vue'
import { useAuthStore, useRecommendationStore } from '../stores/auth'
import dayjs from 'dayjs'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const recStore = useRecommendationStore()

const activeTab = ref<'users' | 'stats' | 'rules' | 'plans'>('users')

// 发布计划管理
const plans = ref<any[]>([])
const loadingPlans = ref(false)
const planKeyword = ref('')
const planFilterSchool = ref('')
const planFilterAgeGroup = ref('')
const planFilterDateRange = ref<string[]>([])

// 提取所有学校选项
const planSchools = computed(() => {
  const schools = new Set<string>()
  plans.value.forEach(p => {
    if (p.school_name) schools.add(p.school_name)
  })
  return Array.from(schools).sort()
})

// 重置筛选条件
const resetPlanFilters = () => {
  planKeyword.value = ''
  planFilterSchool.value = ''
  planFilterAgeGroup.value = ''
  planFilterDateRange.value = []
}

const loadPlans = async () => {
  loadingPlans.value = true
  try {
    const res = await recStore.api.get('/meal_plans/published')
    plans.value = res
  } catch (err: any) {
    ElMessage.error('加载发布计划失败')
  } finally {
    loadingPlans.value = false
  }
}

// 年龄段映射（中文 -> 英文代码）
const ageGroupMap: Record<string, string> = {
  '小学': 'primary',
  '初中低龄': 'junior_low',
  '初中高龄': 'junior_high',
  '高中': 'senior'
}

const filteredPlans = computed(() => {
  return plans.value.filter(p => {
    // 关键字筛选（计划名称）
    const kw = planKeyword.value.trim().toLowerCase()
    if (kw && !(p.name || '').toLowerCase().includes(kw)) {
      return false
    }

    // 学校筛选
    if (planFilterSchool.value && p.school_name !== planFilterSchool.value) {
      return false
    }

    // 年龄段筛选（支持中文和英文匹配）
    if (planFilterAgeGroup.value) {
      const planAgeGroup = p.age_group || ''
      // 计划中的年龄段可能是中文或英文，需要同时比较
      const mappedAgeGroup = ageGroupMap[planAgeGroup] || planAgeGroup
      if (mappedAgeGroup !== planFilterAgeGroup.value && planAgeGroup !== planFilterAgeGroup.value) {
        return false
      }
    }

    // 日期范围筛选
    if (planFilterDateRange.value && planFilterDateRange.value.length === 2) {
      const planDate = p.date
      if (planDate) {
        const startDate = planFilterDateRange.value[0]
        const endDate = planFilterDateRange.value[1]
        if (planDate < startDate || planDate > endDate) {
          return false
        }
      }
    }

    return true
  })
})

const toggleDeliveryStatus = async (plan: any) => {
  try {
    const newStatus = plan.delivery_status === 1 ? 0 : 1
    await recStore.api.put(`/meal_plans/${plan.id}/delivery-status`, { status: newStatus })
    plan.delivery_status = newStatus
    ElMessage.success('配送状态已更新')
  } catch (error: any) {
    ElMessage.error('更新配送状态失败')
  }
}

// 采购需求相关逻辑
const procurementDialogVisible = ref(false)
const selectedPlanForProcurement = ref<any>(null)
const currentProcurementRows = ref<any[]>([])

// 直接从计划导出CSV（不再生成采购单）
const exportPlanCSV = async (plan: any) => {
  try {
    // 解析 meals 字段获取采购信息
    const meals = Array.isArray(plan.meals) ? plan.meals : (typeof plan.meals === 'string' ? JSON.parse(plan.meals || '[]') : [])
    const row = meals.find((m: any) => m && typeof m === 'object' && String(m.meal_type || '').toLowerCase() === '__procurement__')
    const rows = row?.procurement_rows || []
    
    const procurementRows = Array.isArray(rows) 
      ? rows.map((r: any) => ({ ingredient: String(r?.ingredient || '').trim(), total_grams: Number(r?.total_grams) || 0 }))
            .filter((r: any) => r.ingredient)
      : []
    
    if (procurementRows.length === 0) {
      ElMessage.info('该计划暂无采购数据')
      return
    }
    
    // 直接生成并下载CSV
    const header = ['食材', '总采购量(g)']
    const lines = [header.join(',')]
    for (const r of procurementRows) {
      lines.push(`"${r.ingredient}",${r.total_grams}`)
    }
    const csvContent = '\uFEFF' + lines.join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `采购单_${plan.name || plan.id}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    ElMessage.success('CSV导出成功')
  } catch (e: any) {
    ElMessage.error(e?.message || '导出CSV失败')
  }
}

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

// 用户管理对话框
const userDialogVisible = ref(false)
const isEdit = ref(false)
const savingUser = ref(false)
const userForm = reactive({
  id: null as number | null,
  username: '',
  password: '',
  school: '',
  age_group: 'junior_high',
  role: 'user'
})

const showAddUserDialog = () => {
  isEdit.value = false
  userForm.id = null
  userForm.username = ''
  userForm.password = ''
  userForm.school = ''
  userForm.age_group = 'junior_high'
  userForm.role = 'user'
  userDialogVisible.value = true
}

const editUser = (row: any) => {
  isEdit.value = true
  userForm.id = row.id
  userForm.username = row.username
  userForm.password = ''
  userForm.school = row.school || ''
  userForm.age_group = row.age_group || 'junior_high'
  userForm.role = row.role || 'user'
  userDialogVisible.value = true
}

const saveUser = async () => {
  if (!userForm.username) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (!isEdit.value && !userForm.password) {
    ElMessage.warning('请输入密码')
    return
  }

  savingUser.value = true
  try {
    if (isEdit.value && userForm.id) {
      await recStore.api.put(`/auth/users/${userForm.id}`, userForm)
      ElMessage.success('更新成功')
    } else {
      await recStore.api.post('/auth/register', userForm)
      ElMessage.success('创建成功')
    }
    userDialogVisible.value = false
    loadUsers()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  } finally {
    savingUser.value = false
  }
}

const deleteUser = async (userId: number) => {
  try {
    // 简单确认，也可以用 ElMessageBox
    if (!confirm('确定要删除该用户吗？相关数据可能无法恢复')) return
    
    await recStore.api.delete(`/auth/users/${userId}`)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '删除失败')
  }
}

// 用户管理数据
const users = ref<any[]>([])
const userKeyword = ref('')
const loadingUsers = ref(false)
const userEmptyDesc = ref('暂无用户数据。请确认已登录管理员账户，后端已启动且可访问 /auth/admin/users。')
const filteredUsers = computed(() => {
  const kw = userKeyword.value.trim().toLowerCase()
  if (!kw) return users.value
  return users.value.filter(u => 
    (u.username || '').toLowerCase().includes(kw) ||
    (u.school || '').toLowerCase().includes(kw)
  )
})

const userChartRef = ref<HTMLCanvasElement | null>(null)
const dishChartRef = ref<HTMLCanvasElement | null>(null)
let adminChartResizeObserver: ResizeObserver | null = null
let adminChartResizeDebounceTimer: any = null

const setupAdminChartsResizeObserver = () => {
  if (typeof ResizeObserver === 'undefined') return
  const u = userChartRef.value
  const d = dishChartRef.value
  if (!u || !d) return

  // 只用一个 observer，观察两个画布外层容器的变化
  if (adminChartResizeObserver) {
    try {
      adminChartResizeObserver.disconnect()
    } catch (_) {}
    adminChartResizeObserver = null
  }

  adminChartResizeObserver = new ResizeObserver(() => {
    if (adminChartResizeDebounceTimer) clearTimeout(adminChartResizeDebounceTimer)
    adminChartResizeDebounceTimer = setTimeout(() => {
      renderCharts()
    }, 80)
  })

  adminChartResizeObserver.observe(u.parentElement || u)
  adminChartResizeObserver.observe(d.parentElement || d)
}
const statsDays = ref<string[]>([])
const statsActiveUsers = ref<number[]>([])
const statsDishCounts = ref<number[]>([])
const statsRange = ref<number>(14)
const totalDatabaseDishes = ref(0)
const publishedMealPlansCount = ref(0)
const showTooltip = ref(false)
const tooltipX = ref(0)
const tooltipY = ref(0)
const tooltipLabel = ref('')
const tooltipValue = ref('')

type MealKey = 'breakfast' | 'lunch' | 'dinner'
type RuleRow = { category: string; enabled: boolean; count: number }

const categories = [
  '荤菜类',
  '主食类',
  '素菜类',
  '豆制品类',
  '奶及奶制品类',
  '水果类',
  '饮料类',
  '调味料类'
]

const mealPanels: Array<{ key: MealKey; label: string }> = [
  { key: 'breakfast', label: '早餐' },
  { key: 'lunch', label: '午餐' },
  { key: 'dinner', label: '晚餐' }
]

const mealRuleRows = reactive<Record<MealKey, RuleRow[]>>({
  breakfast: categories.map(c => ({ category: c, enabled: false, count: 1 })),
  lunch: categories.map(c => ({ category: c, enabled: false, count: 1 })),
  dinner: categories.map(c => ({ category: c, enabled: false, count: 1 }))
})

const mealCosts = reactive<Record<MealKey, number>>({
  breakfast: 10,
  lunch: 20,
  dinner: 20
})

const mealPeople = reactive<Record<MealKey, number>>({
  breakfast: 1,
  lunch: 1,
  dinner: 1
})

const diningStyle = ref('盘餐') // "团餐" 或 "盘餐"

const loadingRules = ref(false)
const savingRules = ref(false)

const onToggleRule = (row: RuleRow) => {
  if (row.enabled && (!row.count || row.count < 1)) row.count = 1
}

const applyRulesToRows = (data: any) => {
  const rules = (data && typeof data === 'object') ? data : {}
  
  // 处理配餐数量规则
  for (const mealKey of ['breakfast', 'lunch', 'dinner'] as MealKey[]) {
    const mealRules = (rules as any)[mealKey]
    const mealObj = (mealRules && typeof mealRules === 'object') ? mealRules : {}
    for (const row of mealRuleRows[mealKey]) {
      const v = Number((mealObj as any)[row.category] ?? 0)
      if (v > 0) {
        row.enabled = true
        row.count = Math.min(20, Math.max(1, v))
      } else {
        row.enabled = false
        if (!row.count || row.count < 1) row.count = 1
      }
    }
  }

  // 处理配餐成本规则
  const costs = (rules as any).costs || {}
  const people = (rules as any).num_people || {}
  for (const mealKey of ['breakfast', 'lunch', 'dinner'] as MealKey[]) {
    if (typeof costs[mealKey] === 'number') {
      mealCosts[mealKey] = costs[mealKey]
    }
    if (typeof people[mealKey] === 'number') {
      mealPeople[mealKey] = people[mealKey]
    }
  }

  // 处理餐饮形式
  if ((rules as any).dining_style) {
    diningStyle.value = (rules as any).dining_style
  }
}

const buildRulesPayload = () => {
  const payload: any = {
    breakfast: {},
    lunch: {},
    dinner: {},
    costs: { ...mealCosts },
    num_people: { ...mealPeople },
    dining_style: diningStyle.value
  }
  for (const mealKey of ['breakfast', 'lunch', 'dinner'] as MealKey[]) {
    for (const row of mealRuleRows[mealKey]) {
      if (row.enabled) {
        payload[mealKey][row.category] = Math.min(20, Math.max(1, Number(row.count) || 1))
      }
    }
  }
  return payload
}

const loadMealRules = async () => {
  loadingRules.value = true
  try {
    const data = await recStore.api.get('/system/meal-rules')
    applyRulesToRows(data)
    ElMessage.success('规则已加载')
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '加载规则失败')
  } finally {
    loadingRules.value = false
  }
}

const applyMealRules = async () => {
  savingRules.value = true
  try {
    const payload = buildRulesPayload()
    await recStore.api.put('/system/meal-rules', payload)
    ElMessage.success('配置已应用')
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '应用配置失败')
  } finally {
    savingRules.value = false
  }
}

const drawBarChart = (canvas: HTMLCanvasElement, labels: string[], values: number[], color: string) => {
  if (!values || values.length === 0) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  const dpr = window.devicePixelRatio || 1
  const width = canvas.clientWidth
  const height = canvas.clientHeight
  canvas.width = Math.floor(width * dpr)
  canvas.height = Math.floor(height * dpr)
  ctx.scale(dpr, dpr)
  ctx.clearRect(0, 0, width, height)
  const padding = 32
  const w = width - padding * 2
  const h = height - padding * 2
  const maxVRaw = Math.max(1, ...values)
  const tickCount = 4
  const maxV = Math.ceil(maxVRaw / tickCount) * tickCount
  const barW = w / values.length * 0.55
  ctx.fillStyle = '#f9fafb'
  ctx.fillRect(padding, padding, w, h)
  ctx.strokeStyle = '#e5e7eb'
  ctx.lineWidth = 1
  for (let i = 0; i <= tickCount; i++) {
    const gy = padding + h - (h * (i / tickCount))
    ctx.beginPath()
    ctx.moveTo(padding, gy)
    ctx.lineTo(padding + w, gy)
    ctx.stroke()
    ctx.fillStyle = '#6b7280'
    ctx.font = '12px system-ui, -apple-system, Segoe UI, Roboto'
    ctx.textAlign = 'right'
    ctx.textBaseline = 'middle'
    ctx.fillText(String((maxV / tickCount) * i), padding - 8, gy)
  }
  ctx.strokeStyle = '#9ca3af'
  ctx.beginPath()
  ctx.moveTo(padding, padding + h)
  ctx.lineTo(padding + w, padding + h)
  ctx.stroke()
  ctx.fillStyle = '#6b7280'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'top'
  const step = labels.length > 10 ? 2 : 1
  for (let i = 0; i < labels.length; i += step) {
    const lx = padding + i * (w / values.length) + (w / values.length) / 2
    ctx.fillText(labels[i], lx, padding + h + 6)
  }
  for (let i = 0; i < values.length; i++) {
    const x = padding + i * (w / values.length) + (w / values.length - barW) / 2
    const v = values[i]
    const bh = h * (v / maxV)
    const grad = ctx.createLinearGradient(0, padding, 0, padding + h)
    grad.addColorStop(0, '#667eea')
    grad.addColorStop(1, '#764ba2')
    ctx.fillStyle = grad
    ctx.beginPath()
    ctx.roundRect(x, padding + h - bh, barW, bh, 6)
    ctx.fill()
    ctx.shadowColor = 'rgba(102,126,234,0.25)'
    ctx.shadowBlur = 10
    ctx.shadowOffsetY = 2
    ctx.fillStyle = '#111827'
    ctx.font = '12px system-ui, -apple-system, Segoe UI, Roboto'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'bottom'
    const ty = padding + h - bh - 6
    const text = String(v)
    const tw = ctx.measureText(text).width + 12
    const th = 18
    ctx.fillStyle = 'rgba(255,255,255,0.9)'
    ctx.beginPath()
    ctx.roundRect(x + barW / 2 - tw / 2, ty - th, tw, th, 9)
    ctx.fill()
    ctx.fillStyle = '#374151'
    ctx.fillText(text, x + barW / 2, ty - 4)
    ctx.shadowBlur = 0
    ctx.shadowOffsetY = 0
  }
}

const drawLineChart = (canvas: HTMLCanvasElement, labels: string[], values: number[], color: string) => {
  if (!values || values.length === 0) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  const dpr = window.devicePixelRatio || 1
  const width = canvas.clientWidth
  const height = canvas.clientHeight
  canvas.width = Math.floor(width * dpr)
  canvas.height = Math.floor(height * dpr)
  ctx.scale(dpr, dpr)
  ctx.clearRect(0, 0, width, height)
  const padding = 32
  const w = width - padding * 2
  const h = height - padding * 2
  const maxVRaw = Math.max(1, ...values)
  const tickCount = 4
  const maxV = Math.ceil(maxVRaw / tickCount) * tickCount
  ctx.fillStyle = '#f9fafb'
  ctx.fillRect(padding, padding, w, h)
  ctx.strokeStyle = '#e5e7eb'
  ctx.lineWidth = 1
  for (let i = 0; i <= tickCount; i++) {
    const gy = padding + h - (h * (i / tickCount))
    ctx.beginPath()
    ctx.moveTo(padding, gy)
    ctx.lineTo(padding + w, gy)
    ctx.stroke()
    ctx.fillStyle = '#6b7280'
    ctx.font = '12px system-ui, -apple-system, Segoe UI, Roboto'
    ctx.textAlign = 'right'
    ctx.textBaseline = 'middle'
    ctx.fillText(String((maxV / tickCount) * i), padding - 8, gy)
  }
  ctx.strokeStyle = '#9ca3af'
  ctx.beginPath()
  ctx.moveTo(padding, padding + h)
  ctx.lineTo(padding + w, padding + h)
  ctx.stroke()
  ctx.fillStyle = '#6b7280'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'top'
  const step = labels.length > 10 ? 2 : 1
  for (let i = 0; i < labels.length; i += step) {
    const lx = padding + i * (w / (labels.length - 1))
    ctx.fillText(labels[i], lx, padding + h + 6)
  }
  const grad = ctx.createLinearGradient(0, padding, 0, padding + h)
  grad.addColorStop(0, 'rgba(16,185,129,0.25)')
  grad.addColorStop(1, 'rgba(16,185,129,0)')
  ctx.beginPath()
  for (let i = 0; i < values.length; i++) {
    const x = padding + i * (w / (values.length - 1))
    const y = padding + h - (h * (values[i] / maxV))
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  }
  ctx.lineTo(padding + w, padding + h)
  ctx.lineTo(padding, padding + h)
  ctx.closePath()
  ctx.fillStyle = grad
  ctx.fill()
  ctx.strokeStyle = '#10b981'
  ctx.lineWidth = 2
  ctx.beginPath()
  for (let i = 0; i < values.length; i++) {
    const x = padding + i * (w / (values.length - 1))
    const y = padding + h - (h * (values[i] / maxV))
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  }
  ctx.stroke()
  ctx.fillStyle = '#ffffff'
  for (let i = 0; i < values.length; i++) {
    const x = padding + i * (w / (values.length - 1))
    const y = padding + h - (h * (values[i] / maxV))
    ctx.beginPath()
    ctx.arc(x, y, 3, 0, Math.PI * 2)
    ctx.fill()
    ctx.strokeStyle = '#10b981'
    ctx.lineWidth = 2
    ctx.stroke()
    ctx.fillStyle = '#374151'
    ctx.font = '12px system-ui, -apple-system, Segoe UI, Roboto'
    ctx.textAlign = 'center'
    const ty = Math.max(padding + 12, y - 8)
    ctx.fillText(String(values[i]), x, ty)
    ctx.fillStyle = '#ffffff'
  }
}

const renderCharts = () => {
  if (userChartRef.value) {
    drawLineChart(userChartRef.value, statsDays.value, statsActiveUsers.value, '#10b981')
  }
  if (dishChartRef.value) {
    drawBarChart(dishChartRef.value, statsDays.value, statsDishCounts.value, '#667eea')
  }
  attachChartEvents()
  setupAdminChartsResizeObserver()
}

const loadStats = async () => {
  try {
    const data = await recStore.adminGetDishStats(statsRange.value)
    statsDays.value = (data?.days || []).map((d: string) => dayjs(d).format('MM-DD'))
    statsActiveUsers.value = data?.active_user_counts || []
    statsDishCounts.value = data?.new_dish_counts || [] // 后端已改为 new_dish_counts
    
    totalDatabaseDishes.value = data?.totals?.total_database_dishes || 0
    publishedMealPlansCount.value = data?.totals?.total_published_meal_plans || 0
    
    await nextTick()
    renderCharts()
  } catch (_err) {
  }
}

watch(activeTab, async (tab) => {
  if (tab === 'stats') {
    await nextTick()
    renderCharts()
  }
  if (tab === 'rules') {
    await loadMealRules()
  }
  if (tab === 'plans') {
    await loadPlans()
  }
})

watch(statsRange, async () => {
  await loadStats()
})

const attachChartEvents = () => {
  const padding = 32
  if (userChartRef.value) {
    const canvas = userChartRef.value
    const onMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect()
      const x = e.clientX - rect.left
      const width = canvas.clientWidth
      const height = canvas.clientHeight
      const w = width - padding * 2
      if (statsDays.value.length <= 1) return
      const step = w / (statsDays.value.length - 1)
      const i = Math.max(0, Math.min(statsDays.value.length - 1, Math.round((x - padding) / step)))
      tooltipLabel.value = statsDays.value[i]
      tooltipValue.value = String(statsActiveUsers.value[i] ?? 0)
      tooltipX.value = e.clientX + 12
      tooltipY.value = e.clientY + 12
      showTooltip.value = true
    }
    const onLeave = () => { showTooltip.value = false }
    canvas.onmousemove = onMove
    canvas.onmouseleave = onLeave
  }
  if (dishChartRef.value) {
    const canvas = dishChartRef.value
    const onMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect()
      const x = e.clientX - rect.left
      const width = canvas.clientWidth
      const height = canvas.clientHeight
      const w = width - padding * 2
      const segment = w / (statsDays.value.length || 1)
      let i = Math.floor((x - padding) / segment)
      i = Math.max(0, Math.min(statsDays.value.length - 1, i))
      tooltipLabel.value = statsDays.value[i]
      tooltipValue.value = String(statsDishCounts.value[i] ?? 0)
      tooltipX.value = e.clientX + 12
      tooltipY.value = e.clientY + 12
      showTooltip.value = true
    }
    const onLeave = () => { showTooltip.value = false }
    canvas.onmousemove = onMove
    canvas.onmouseleave = onLeave
  }
}

// 加载用户列表
const loadUsers = async () => {
  loadingUsers.value = true
  try {
    const data = await authStore.adminListUsers()
    users.value = data || []
    if (users.value.length === 0) {
      userEmptyDesc.value = '暂无用户数据。'
    }
  } catch (err: any) {
    const status = err?.response?.status
    if (status === 403) {
      userEmptyDesc.value = '无权限访问，请使用管理员账户登录。'
    } else if (status === 401) {
      userEmptyDesc.value = '登录状态无效，请重新登录。'
    } else {
      userEmptyDesc.value = err.response?.data?.detail || '加载用户失败'
    }
    ElMessage.error(userEmptyDesc.value)
  } finally {
    loadingUsers.value = false
  }
}

onMounted(async () => {
  await loadUsers()
  await loadStats()
  window.addEventListener('resize', renderCharts)
  window.addEventListener('layout-resize', renderCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', renderCharts)
  window.removeEventListener('layout-resize', renderCharts)
  if (adminChartResizeObserver) {
    try {
      adminChartResizeObserver.disconnect()
    } catch (_) {}
    adminChartResizeObserver = null
  }
})
</script>

<style scoped>
.admin-container {
  width: 100%;
  min-height: 100%;
}
.main-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 1400px;
  margin: 0 auto;
}
.header-section {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 8px 20px rgba(0,0,0,0.06);
}
.admin-tabs {
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 8px 20px rgba(0,0,0,0.06);
}
.toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  text-align: center;
}
.stat-value {
  font-size: 32px;
  font-weight: 700;
}
.stat-label {
  color: #666;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 16px;
}

.chart-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  position: relative;
}

.chart-title {
  font-weight: 600;
  margin-bottom: 8px;
}

.chart-canvas {
  width: 100%;
  height: 240px;
  display: block;
}

.chart-tooltip {
  position: fixed;
  z-index: 1000;
  background: #111827;
  color: #fff;
  padding: 8px 10px;
  border-radius: 8px;
  box-shadow: 0 6px 16px rgba(0,0,0,0.18);
  font-size: 12px;
  pointer-events: none;
}
.chart-tooltip .tooltip-title {
  opacity: 0.85;
}
.chart-tooltip .tooltip-value {
  font-weight: 600;
  margin-top: 2px;
}

/* 发布计划操作按钮样式 - 与历史菜谱页面统一 */
.plan-actions-row {
  display: flex;
  flex-wrap: nowrap;
  gap: 6px;
  white-space: nowrap;
}

.plan-btn {
  border-radius: 6px;
  font-weight: 500;
  padding: 6px 10px;
  margin-left: 0 !important;
}

.plan-btn-procurement {
  background-color: #f4f7fb !important;
  border-color: #dce4ee !important;
  color: #5a7a9e !important;
}
.plan-btn-procurement:hover,
.plan-btn-procurement:focus {
  background-color: #e8eef6 !important;
  border-color: #c9d6e8 !important;
  color: #4a6585 !important;
}

.plan-btn-deliver {
  background-color: #f0f8f4 !important;
  border-color: #d8ebe1 !important;
  color: #5f8f75 !important;
}
.plan-btn-deliver:hover,
.plan-btn-deliver:focus {
  background-color: #e5f3eb !important;
  border-color: #cde5d8 !important;
  color: #4f7b65 !important;
}

.plan-btn-undeliver {
  background-color: #faf6f0 !important;
  border-color: #e8e0d6 !important;
  color: #8b7355 !important;
}
.plan-btn-undeliver:hover,
.plan-btn-undeliver:focus {
  background-color: #f3ebe0 !important;
  border-color: #ddd2c4 !important;
  color: #6b5a45 !important;
}

/* 导出CSV - 蓝色系 */
.plan-btn-export {
  background-color: #f0f7ff !important;
  border-color: #d6e4f7 !important;
  color: #5a7db5 !important;
}
.plan-btn-export:hover,
.plan-btn-export:focus {
  background-color: #e5f0fc !important;
  border-color: #c5d8f0 !important;
  color: #4a6a9e !important;
}
</style>

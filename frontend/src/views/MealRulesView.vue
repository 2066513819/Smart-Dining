<template>
  <div class="meal-rules-view">
    <main class="main-content">
      <section class="header-section">
        <h2>餐饮设置</h2>
        <p>配置早、中、晚餐的配餐规则与成本参数，用于菜谱制定时的推荐与计算</p>
      </section>

      <div class="rules-content">
        <div class="toolbar" style="justify-content: space-between; align-items: center;">
          <div class="rule-title" style="font-size: 16px; font-weight: 600; color: #374151;">配餐规则与成本设置</div>
          <div style="display: flex; gap: 12px;">
            <el-button @click="loadMealRules" :loading="loadingRules">加载规则</el-button>
            <el-button type="primary" @click="applyMealRules" :loading="savingRules" size="large" style="padding: 0 32px;">应用配置</el-button>
          </div>
        </div>

        <!-- 餐饮形式设置 -->
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

        <!-- 每餐成本设置 -->
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

        <!-- 早中晚类别与数量 -->
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
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRecommendationStore } from '../stores/auth'
import { ElMessage } from 'element-plus'

const recStore = useRecommendationStore()

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

const diningStyle = ref('盘餐')

const loadingRules = ref(false)
const savingRules = ref(false)

const onToggleRule = (row: RuleRow) => {
  if (row.enabled && (!row.count || row.count < 1)) row.count = 1
}

const applyRulesToRows = (data: any) => {
  const rules = (data && typeof data === 'object') ? data : {}

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

onMounted(() => {
  loadMealRules()
})
</script>

<style scoped>
.meal-rules-view {
  padding: 0;
  background-color: #f5f7fa;
  min-height: calc(100vh - 120px);
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.header-section {
  margin-bottom: 24px;
}

.header-section h2 {
  font-size: 22px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 8px 0;
}

.header-section p {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.rules-content {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
}
</style>

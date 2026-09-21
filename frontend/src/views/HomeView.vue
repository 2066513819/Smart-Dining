<template>
  <div class="home-simple">
    <div class="header">
      <div>
        <h2>已发布食谱计划</h2>
        <p>默认展示最近一次发布的菜谱计划，可按日期范围查看营养占比</p>
      </div>
      <div>
        <el-button type="primary" @click="refresh">刷新</el-button>
      </div>
    </div>

    <div class="content">
      <el-skeleton :loading="loading" animated>
        <template #template>
          <el-skeleton-item variant="image" style="width:100%;height:120px" />
        </template>

        <div v-if="!loading && plans.length===0" class="empty-wrap">
          <el-empty description="暂无已发布计划" />
        </div>

        <template v-if="latestPlan">
          <!-- AI 营养分析报告展示区域 -->
          <section v-if="currentPlanAnalysis" class="ai-analysis-section">
            <div class="ai-analysis-card">
              <div class="ai-analysis-header">
                <el-icon color="#409eff" :size="20"><Opportunity /></el-icon>
                <span class="ai-title">智能管家：营养分析与建议</span>
              </div>
              <div class="ai-analysis-content">
                <pre class="ai-text">{{ currentPlanAnalysis }}</pre>
              </div>
            </div>
          </section>

          <section class="chart-section">
            <div class="chart-head">
              <div class="chart-title">营养占比（按日期范围汇总）</div>
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                unlink-panels
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                :clearable="false"
                style="max-width: 360px;"
              />
            </div>
            <div class="chart-body">
              <div class="chart-canvas-wrap">
                <canvas ref="nutritionChartRef" class="chart-canvas"></canvas>
              </div>
              <div class="chart-legend">
                <div class="legend-row">
                  <span class="dot dot-protein"></span>
                  <span>蛋白质</span>
                  <span class="legend-val">{{ chartSummary.proteinPct }}%</span>
                </div>
                <div class="legend-row">
                  <span class="dot dot-fat"></span>
                  <span>脂肪</span>
                  <span class="legend-val">{{ chartSummary.fatPct }}%</span>
                </div>
                <div class="legend-row">
                  <span class="dot dot-carbs"></span>
                  <span>碳水</span>
                  <span class="legend-val">{{ chartSummary.carbsPct }}%</span>
                </div>
                <div class="legend-sub">
                  <div>统计范围：{{ dateRangeText }}</div>
                  <div>总能量（估算）：{{ chartSummary.totalKcal }} kcal</div>
                </div>
              </div>
            </div>
          </section>

          <section class="plan-section">
            <div class="plan-head">
              <div>
                <div class="plan-name">{{ latestPlan.name }}</div>
                <div class="plan-meta">
                  <span v-if="authStore.user?.role === 'admin'" style="margin-right: 12px; font-weight: bold; color: #409eff;">{{ latestPlan.school_name || '未知学校' }}</span>
                  发布：{{ formatPlanDate(latestPlan.published_at || latestPlan.date) }}
                </div>
              </div>
              <el-tag type="info" effect="plain">{{ latestPlan.age_group }}</el-tag>
            </div>

            <el-table
              :data="latestGroupedRows"
              stripe
              border
              style="width: 100%"
              class="csv-style-table"
            >
              <el-table-column prop="day" label="时间" width="140">
                <template #default="scope">
                  <div class="day-cell">
                    <div class="day-cell-title">第{{ scope.row.day }}天</div>
                    <div v-if="scope.row.apply_date" class="day-cell-date">
                      {{ formatApplyDate(scope.row.apply_date) }}
                    </div>
                  </div>
                </template>
              </el-table-column>
              
              <el-table-column label="早餐" min-width="320">
                <template #default="scope">
                  <div v-if="scope.row.breakfast && scope.row.breakfast.length > 0" class="meal-cell-container">
                    <table class="meal-dish-table">
                      <thead>
                        <tr>
                          <th width="100">类型</th>
                          <th>菜品详情</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="dish in scope.row.breakfast" :key="dish.id">
                          <td class="category-td">
                            <el-tag size="small" type="success" effect="light" v-if="dish.dish_type">{{ dishTypeToText(dish.dish_type) }}</el-tag>
                            <el-tag size="small" type="info" effect="light" v-else-if="dish.meal_type">{{ dish.meal_type }}</el-tag>
                            <span v-else>-</span>
                          </td>
                          <td class="details-td">
                            <div class="dish-name-row">
                              <el-tooltip placement="top" effect="light">
                                <template #content>
                                  <div class="dish-tooltip-content">
                                    <div class="tooltip-section">
                                      <div class="tooltip-title">配方/描述：</div>
                                      <div class="tooltip-text">{{ dish.dish_recipe || '暂无描述' }}</div>
                                    </div>
                                    <div class="tooltip-section">
                                      <div class="tooltip-title">营养指标：</div>
                                      <div class="tooltip-text">{{ dish.nutrition }}</div>
                                    </div>
                                  </div>
                                </template>
                                <span class="clickable-dish-name">{{ dish.dish_name }}</span>
                              </el-tooltip>
                              <span class="dish-tags">
                                <span class="servings-text">{{ dish.servings || 1 }}份</span>
                                <el-tag size="small" type="info" effect="plain">{{ dish.flavor || '原味' }}</el-tag>
                              </span>
                            </div>
                          </td>
                        </tr>
                      </tbody>
                      <tfoot>
                        <tr>
                          <td colspan="2" class="meal-summary-td">
                            <div class="meal-total-energy">
                              能量总和：<span>{{ calculateMealEnergy(scope.row.breakfast) }} kcal</span>
                            </div>
                          </td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                  <span v-else class="meal-empty">-</span>
                </template>
              </el-table-column>

              <el-table-column label="午餐" min-width="320">
                <template #default="scope">
                  <div v-if="scope.row.lunch && scope.row.lunch.length > 0" class="meal-cell-container">
                    <table class="meal-dish-table">
                      <thead>
                        <tr>
                          <th width="100">类型</th>
                          <th>菜品详情</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="dish in scope.row.lunch" :key="dish.id">
                          <td class="category-td">
                            <el-tag size="small" type="success" effect="light" v-if="dish.dish_type">{{ dishTypeToText(dish.dish_type) }}</el-tag>
                            <el-tag size="small" type="info" effect="light" v-else-if="dish.meal_type">{{ dish.meal_type }}</el-tag>
                            <span v-else>-</span>
                          </td>
                          <td class="details-td">
                            <div class="dish-name-row">
                              <el-tooltip placement="top" effect="light">
                                <template #content>
                                  <div class="dish-tooltip-content">
                                    <div class="tooltip-section">
                                      <div class="tooltip-title">配方/描述：</div>
                                      <div class="tooltip-text">{{ dish.dish_recipe || '暂无描述' }}</div>
                                    </div>
                                    <div class="tooltip-section">
                                      <div class="tooltip-title">营养指标：</div>
                                      <div class="tooltip-text">{{ dish.nutrition }}</div>
                                    </div>
                                  </div>
                                </template>
                                <span class="clickable-dish-name">{{ dish.dish_name }}</span>
                              </el-tooltip>
                              <span class="dish-tags">
                                <span class="servings-text">{{ dish.servings || 1 }}份</span>
                                <el-tag size="small" type="info" effect="plain">{{ dish.flavor || '原味' }}</el-tag>
                              </span>
                            </div>
                          </td>
                        </tr>
                      </tbody>
                      <tfoot>
                        <tr>
                          <td colspan="2" class="meal-summary-td">
                            <div class="meal-total-energy">
                              能量总和：<span>{{ calculateMealEnergy(scope.row.lunch) }} kcal</span>
                            </div>
                          </td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                  <span v-else class="meal-empty">-</span>
                </template>
              </el-table-column>

              <el-table-column label="晚餐" min-width="320">
                <template #default="scope">
                  <div v-if="scope.row.dinner && scope.row.dinner.length > 0" class="meal-cell-container">
                    <table class="meal-dish-table">
                      <thead>
                        <tr>
                          <th width="100">类型</th>
                          <th>菜品详情</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="dish in scope.row.dinner" :key="dish.id">
                          <td class="category-td">
                            <el-tag size="small" type="success" effect="light" v-if="dish.dish_type">{{ dishTypeToText(dish.dish_type) }}</el-tag>
                            <el-tag size="small" type="info" effect="light" v-else-if="dish.meal_type">{{ dish.meal_type }}</el-tag>
                            <span v-else>-</span>
                          </td>
                          <td class="details-td">
                            <div class="dish-name-row">
                              <el-tooltip placement="top" effect="light">
                                <template #content>
                                  <div class="dish-tooltip-content">
                                    <div class="tooltip-section">
                                      <div class="tooltip-title">配方/描述：</div>
                                      <div class="tooltip-text">{{ dish.dish_recipe || '暂无描述' }}</div>
                                    </div>
                                    <div class="tooltip-section">
                                      <div class="tooltip-title">营养指标：</div>
                                      <div class="tooltip-text">{{ dish.nutrition }}</div>
                                    </div>
                                  </div>
                                </template>
                                <span class="clickable-dish-name">{{ dish.dish_name }}</span>
                              </el-tooltip>
                              <span class="dish-tags">
                                <span class="servings-text">{{ dish.servings || 1 }}份</span>
                                <el-tag size="small" type="info" effect="plain">{{ dish.flavor || '原味' }}</el-tag>
                              </span>
                            </div>
                          </td>
                        </tr>
                      </tbody>
                      <tfoot>
                        <tr>
                          <td colspan="2" class="meal-summary-td">
                            <div class="meal-total-energy">
                              能量总和：<span>{{ calculateMealEnergy(scope.row.dinner) }} kcal</span>
                            </div>
                          </td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                  <span v-else class="meal-empty">-</span>
                </template>
              </el-table-column>
            </el-table>

            <div v-if="latestProcurementRows.length > 0" class="procurement-section">
              <div class="procurement-head" @click="isProcurementExpanded = !isProcurementExpanded">
                <div class="procurement-title">配方采购表</div>
                <div class="procurement-actions">
                  <el-button size="small" type="primary" plain @click.stop="exportProcurementCSV">导出</el-button>
                  <div class="procurement-tip">{{ isProcurementExpanded ? '收起' : '展开' }}</div>
                </div>
              </div>
              <el-collapse-transition>
                <div v-show="isProcurementExpanded">
                  <el-table :data="latestProcurementRows" stripe border style="width: 100%; margin-top: 10px;">
                    <el-table-column prop="ingredient" label="食材" min-width="240" />
                    <el-table-column prop="total_grams" label="总采购量(g)" width="180">
                      <template #default="scope">{{ Number(scope.row.total_grams || 0).toFixed(1) }}</template>
                    </el-table-column>
                  </el-table>
                </div>
              </el-collapse-transition>
            </div>
          </section>
        </template>
      </el-skeleton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { Opportunity } from '@element-plus/icons-vue'
import { useRecommendationStore, useAuthStore } from '../stores/auth'
import { dishTypeToText } from '../utils/constants'

const recommendationStore = useRecommendationStore()
const authStore = useAuthStore()

const loading = ref(false)
const plans = ref<any[]>([])
const latestPlan = computed(() => (plans.value && plans.value.length > 0 ? plans.value[0] : null))
const isProcurementExpanded = ref(true)

const currentPlanAnalysis = ref('')
let analysisTimer: any = null

const checkLocalAnalysis = (planId: string | number) => {
  if (!planId || !authStore.user?.id) return
  const userId = authStore.user.id
  const storageKey = `plan_analysis_${userId}_${planId}`
  const analysis = localStorage.getItem(storageKey)
  if (analysis) {
    currentPlanAnalysis.value = analysis
    if (analysisTimer) {
      clearTimeout(analysisTimer)
      analysisTimer = null
    }
  } else {
    // 如果还没分析完，每隔3秒检查一次，最多检查10次（30秒）
    let count = 0
    const poll = () => {
      const a = localStorage.getItem(storageKey)
      if (a) {
        currentPlanAnalysis.value = a
        analysisTimer = null
      } else if (count < 10) {
        count++
        analysisTimer = setTimeout(poll, 3000)
      }
    }
    if (analysisTimer) clearTimeout(analysisTimer)
    analysisTimer = setTimeout(poll, 3000)
  }
}

const fetchPlans = async () => {
  loading.value = true
  plans.value = []
  try {
    console.log('开始获取已发布计划...')
    const raw = await recommendationStore.getPublishedMealPlans()
    console.log('获取到的原始计划:', raw)
    if (!Array.isArray(raw) || raw.length === 0) {
      console.log('没有找到已发布计划')
      return
    }
    plans.value = raw
    initRangeFromLatest()
    if (latestPlan.value?.id) {
      checkLocalAnalysis(latestPlan.value.id)
    }
  } catch (e) { console.error('fetchPlans error', e); plans.value = [] }
  finally { loading.value = false }
}

const refresh = async () => { await fetchPlans() }
onMounted(async () => { await fetchPlans() })

const pad2 = (n: number) => String(n).padStart(2, '0')

const parseYMD = (s: string) => {
  const m = String(s || '').match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (!m) return null
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
  return isNaN(d.getTime()) ? null : d
}

const formatYMD = (d: Date) => `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`

const addDaysYMD = (ymd: string, days: number) => {
  const base = parseYMD(ymd)
  if (!base) return ymd
  const d = new Date(base.getFullYear(), base.getMonth(), base.getDate())
  d.setDate(d.getDate() + Number(days || 0))
  return formatYMD(d)
}

const parseDateSmart = (val: any) => {
  if (!val) return null
  if (val instanceof Date) return isNaN(val.getTime()) ? null : val
  const s = String(val)
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (m) return parseYMD(s)
  const d = new Date(s)
  return isNaN(d.getTime()) ? null : d
}

const weekdayCN = (d: Date) => {
  const idx = d.getDay()
  return ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][idx] || ''
}

const formatPlanDate = (val: any) => {
  const d = parseDateSmart(val)
  if (!d) return val ? String(val) : '-'
  const ymd = formatYMD(d)
  const w = weekdayCN(d)
  const s = String(val || '')
  const showTime = s.includes('T') || s.includes(':')
  if (!showTime) return w ? `${ymd}（${w}）` : ymd
  
  // 确保使用北京时间显示小时和分钟
  const hm = d.toLocaleTimeString('zh-CN', { 
    timeZone: 'Asia/Shanghai', 
    hour12: false, 
    hour: '2-digit', 
    minute: '2-digit' 
  })
  return w ? `${ymd} ${hm}（${w}）` : `${ymd} ${hm}`
}

const formatApplyDate = (ymd: string) => {
  const d = parseYMD(ymd)
  if (!d) return String(ymd || '')
  const w = weekdayCN(d)
  return w ? `${ymd}（${w}）` : ymd
}

const normalizeMealType = (v: any) => {
  const s = String(v || '')
  if (s === '早餐' || s === '午餐' || s === '晚餐') return s
  const lc = s.toLowerCase()
  if (lc.includes('breakfast')) return '早餐'
  if (lc.includes('lunch')) return '午餐'
  if (lc.includes('dinner')) return '晚餐'
  return s
}

const parseMealsRaw = (p: any) => {
  try {
    return Array.isArray(p?.meals) ? p.meals : (typeof p?.meals === 'string' ? JSON.parse(p.meals || '[]') : [])
  } catch {
    return []
  }
}

const extractProcurementRows = (plan: any) => {
  if (!plan) return []
  const meals = parseMealsRaw(plan)
  const row = meals.find((m: any) => m && typeof m === 'object' && String(m.meal_type || '').toLowerCase() === '__procurement__')
  const rows = row?.procurement_rows
  if (!Array.isArray(rows)) return []
  return rows
    .map((r: any) => ({ ingredient: String(r?.ingredient || '').trim(), total_grams: Number(r?.total_grams) || 0 }))
    .filter((r: any) => r.ingredient)
}

const latestProcurementRows = computed(() => extractProcurementRows(latestPlan.value))

const exportProcurementCSV = () => {
  const rows = latestProcurementRows.value || []
  if (!rows || rows.length === 0) {
    ElMessage.warning('当前采购表为空')
    return
  }

  const header = ['食材', '总采购量(g)']
  const lines = [header.join(',')]
  for (const r of rows) {
    const ing = String(r?.ingredient || '').replace(/"/g, '""')
    const val = (Number(r?.total_grams) || 0).toFixed(1)
    lines.push(`"${ing}",${val}`)
  }
  const csvContent = '\ufeff' + lines.join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')

  const ymd = (() => {
    const raw = String(latestPlan.value?.date || latestPlan.value?.published_at || '')
    const m = raw.match(/^(\d{4})-(\d{2})-(\d{2})/)
    return m ? `${m[1]}${m[2]}${m[3]}` : ''
  })()
  const now = new Date()
  const pad2 = (n: number) => String(n).padStart(2, '0')
  const today = `${now.getFullYear()}${pad2(now.getMonth() + 1)}${pad2(now.getDate())}`
  const stamp = `${pad2(now.getHours())}${pad2(now.getMinutes())}`

  const suffix = ymd || today
  a.href = url
  a.download = `配方采购表_${suffix}_${stamp}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  ElMessage.success('已导出采购表')
}

const getMealApplyDate = (plan: any, meal: any) => {
  const direct = meal?.apply_date
  if (typeof direct === 'string' && parseYMD(direct)) return direct
  const base = plan?.date
  const day = meal?.day
  if (typeof base === 'string' && parseYMD(base) && typeof day === 'number') {
    return addDaysYMD(base, Math.max(0, day - 1))
  }
  if (typeof base === 'string' && parseYMD(base)) return base
  return ''
}

const parseNumber = (re: RegExp, text: string) => {
  const m = String(text || '').match(re)
  if (!m) return null
  const v = Number(m[1])
  return Number.isFinite(v) ? v : null
}

const parseMacrosFromText = (text: string) => {
  const t = String(text || '')
  const protein = parseNumber(/蛋白质\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)/, t) ?? 0
  const fat = parseNumber(/脂肪\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)/, t) ?? 0
  const carbs = parseNumber(/(?:碳水化合物|碳水)\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)/, t) ?? 0
  const kcal = parseNumber(/(?:能量|卡路里|热量)\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)/, t) ?? 0
  return { protein, fat, carbs, kcal }
}

const macrosOfMeal = (m: any) => {
  const protein = Number(m?.total_protein) || 0
  const fat = Number(m?.total_fat) || 0
  const carbs = Number(m?.total_carbohydrates) || 0
  const kcal = Number(m?.total_calories) || 0
  if (protein || fat || carbs || kcal) return { protein, fat, carbs, kcal }
  const t = String(m?.nutrition || m?.calories || '')
  return parseMacrosFromText(t)
}

const latestGroupedRows = computed(() => {
  const p = latestPlan.value
  if (!p) return []
  const meals = parseMealsRaw(p)
  const map: Record<number, any> = {}
  for (const raw of meals) {
    if (!raw || typeof raw !== 'object') continue
    if (String(raw.meal_type || '').toLowerCase() === '__procurement__') continue
    const day = Number(raw.day) || 1
    const apply_date = getMealApplyDate(p, raw)
    if (!map[day]) map[day] = { day, apply_date: apply_date || null, breakfast: [], lunch: [], dinner: [] }
    if (!map[day].apply_date && apply_date) map[day].apply_date = apply_date
    const mt = normalizeMealType(raw.meal_type || raw.time)
    
    // 智能提取类型：优先取分类字段，如果没有则取非餐次名称的 dish_type
    let displayType = raw.category || raw.dish_type || raw.type || raw.kind || ''
    // 如果提取出的类型正好等于餐次名称（如 "早餐"），且没有其他分类信息，则尝试找找有没有其他信息
    if (displayType === mt) {
      displayType = raw.category || ''
    }

    const item = {
      ...raw,
      dish_name: raw.name || raw.dish_name || '未知菜品',
      dish_recipe: raw.dish_recipe || raw.recipe || raw.description || raw.ingredients || '',
      meal_type: mt,
      dish_type: displayType,
      nutrition: raw.nutrition || raw.calories || raw.energy || '',
      servings: Number(raw.servings) || 1
    }
    if (mt === '早餐') map[day].breakfast.push(item)
    else if (mt === '午餐') map[day].lunch.push(item)
    else if (mt === '晚餐') map[day].dinner.push(item)
  }
  return Object.values(map).sort((a: any, b: any) => a.day - b.day)
})

// 计算单餐次能量总和
const calculateMealEnergy = (dishes: any[]) => {
  if (!dishes || dishes.length === 0) return 0
  let total = 0
  dishes.forEach(dish => {
    const nutrition = dish.nutrition || ''
    const match = nutrition.match(/(?:卡路里|能量|能量)[:：]\s*(\d+(?:\.\d+)?)/)
    if (match && match[1]) {
      total += parseFloat(match[1]) * (Number(dish.servings) || 1)
    }
  })
  return total.toFixed(1)
}

const dateRange = ref<[string, string] | []>([])

const initRangeFromLatest = () => {
  const p = latestPlan.value
  if (!p) return
  const meals = parseMealsRaw(p)
  const dates = meals
    .filter((m: any) => !(m && typeof m === 'object' && String(m.meal_type || '').toLowerCase() === '__procurement__'))
    .map((m: any) => getMealApplyDate(p, m))
    .filter((v: any) => typeof v === 'string' && parseYMD(v))
    .sort()
  const start = dates[0] || (typeof p?.date === 'string' ? p.date : '')
  const end = dates[dates.length - 1] || start
  if (start && end) dateRange.value = [start, end]
}

const dateRangeText = computed(() => {
  if (!Array.isArray(dateRange.value) || dateRange.value.length !== 2) return '-'
  return `${dateRange.value[0]} 至 ${dateRange.value[1]}`
})

const chartSummary = computed(() => {
  if (!Array.isArray(dateRange.value) || dateRange.value.length !== 2) {
    return { proteinPct: 0, fatPct: 0, carbsPct: 0, totalKcal: 0, proteinKcal: 0, fatKcal: 0, carbsKcal: 0 }
  }
  const [start, end] = dateRange.value
  const inRange = (ymd: string) => ymd && ymd >= start && ymd <= end
  let proteinG = 0
  let fatG = 0
  let carbsG = 0
  const p = latestPlan.value
  if (p) {
    const meals = parseMealsRaw(p)
    for (const m of meals) {
      if (!m || typeof m !== 'object') continue
      const apply_date = getMealApplyDate(p, m)
      if (!apply_date || !parseYMD(apply_date) || !inRange(apply_date)) continue
      const mac = macrosOfMeal(m)
      proteinG += Number(mac.protein || 0)
      fatG += Number(mac.fat || 0)
      carbsG += Number(mac.carbs || 0)
    }
  }
  const proteinKcal = proteinG * 4
  const carbsKcal = carbsG * 4
  const fatKcal = fatG * 9
  const totalKcal = Math.max(0, proteinKcal + carbsKcal + fatKcal)
  const pct = (v: number) => (totalKcal > 0 ? Math.round((v / totalKcal) * 100) : 0)
  let proteinPct = pct(proteinKcal)
  let fatPct = pct(fatKcal)
  let carbsPct = pct(carbsKcal)
  const sum = proteinPct + fatPct + carbsPct
  if (sum !== 100 && totalKcal > 0) {
    const rest = 100 - sum
    const maxKey = proteinKcal >= fatKcal && proteinKcal >= carbsKcal ? 'p' : (fatKcal >= carbsKcal ? 'f' : 'c')
    if (maxKey === 'p') proteinPct += rest
    else if (maxKey === 'f') fatPct += rest
    else carbsPct += rest
  }
  return {
    proteinPct,
    fatPct,
    carbsPct,
    totalKcal: Math.round(totalKcal),
    proteinKcal: Math.round(proteinKcal),
    fatKcal: Math.round(fatKcal),
    carbsKcal: Math.round(carbsKcal)
  }
})

const nutritionChartRef = ref<HTMLCanvasElement | null>(null)
let nutritionResizeObserver: ResizeObserver | null = null
let nutritionResizeDebounceTimer: any = null

const setupNutritionChartResizeObserver = () => {
  const canvas = nutritionChartRef.value
  if (!canvas) return
  if (typeof ResizeObserver === 'undefined') return

  // 目标优先用外层容器：宽度通常是在容器上变化
  const target = canvas.parentElement || canvas

  // 只要目标变了就重新挂载
  if (nutritionResizeObserver) {
    try {
      nutritionResizeObserver.disconnect()
    } catch (_) {}
    nutritionResizeObserver = null
  }

  nutritionResizeObserver = new ResizeObserver(() => {
    if (nutritionResizeDebounceTimer) clearTimeout(nutritionResizeDebounceTimer)
    nutritionResizeDebounceTimer = setTimeout(() => {
      redraw()
    }, 60)
  })

  nutritionResizeObserver.observe(target)
}

const drawPie = (canvas: HTMLCanvasElement, parts: Array<{ value: number; color: string }>) => {
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  const dpr = window.devicePixelRatio || 1
  const width = canvas.clientWidth || 260
  const height = canvas.clientHeight || 260
  canvas.width = Math.floor(width * dpr)
  canvas.height = Math.floor(height * dpr)
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
  ctx.clearRect(0, 0, width, height)

  const total = Math.max(0, parts.reduce((s, p) => s + Math.max(0, p.value), 0))
  const cx = width / 2
  const cy = height / 2
  const r = Math.min(width, height) / 2 - 8
  const innerR = r * 0.62

  ctx.fillStyle = '#f9fafb'
  ctx.beginPath()
  ctx.arc(cx, cy, r, 0, Math.PI * 2)
  ctx.fill()

  if (total <= 0) {
    ctx.fillStyle = '#9ca3af'
    ctx.font = '13px system-ui, -apple-system, Segoe UI, Roboto'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText('暂无数据', cx, cy)
    return
  }

  let start = -Math.PI / 2
  for (const p of parts) {
    const v = Math.max(0, p.value)
    if (!v) continue
    const ang = (v / total) * Math.PI * 2
    ctx.beginPath()
    ctx.moveTo(cx, cy)
    ctx.arc(cx, cy, r, start, start + ang)
    ctx.closePath()
    ctx.fillStyle = p.color
    ctx.fill()
    start += ang
  }

  ctx.globalCompositeOperation = 'destination-out'
  ctx.beginPath()
  ctx.arc(cx, cy, innerR, 0, Math.PI * 2)
  ctx.fill()
  ctx.globalCompositeOperation = 'source-over'

  // 绘制中心文字
  const totalKcal = Math.round(chartSummary.value.totalKcal)
  
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  
  // 第一行：标题
  ctx.fillStyle = '#111827'
  ctx.font = 'bold 16px system-ui, -apple-system, sans-serif'
  ctx.fillText('营养占比', cx, cy - 12)
  
  // 第二行：数值
  ctx.fillStyle = '#6b7280'
  ctx.font = '500 14px system-ui, -apple-system, sans-serif'
  ctx.fillText(`${totalKcal} kcal`, cx, cy + 14)
}

const redraw = async () => {
  await nextTick()
  const canvas = nutritionChartRef.value
  if (!canvas) return
  setupNutritionChartResizeObserver()
  drawPie(canvas, [
    { value: chartSummary.value.proteinKcal, color: '#67c23a' },
    { value: chartSummary.value.fatKcal, color: '#f56c6c' },
    { value: chartSummary.value.carbsKcal, color: '#e6a23c' }
  ])
}

watch(() => [chartSummary.value.totalKcal, chartSummary.value.proteinKcal, chartSummary.value.fatKcal, chartSummary.value.carbsKcal], () => { redraw() })
watch(() => dateRange.value, () => { redraw() }, { deep: true })
watch(() => latestPlan.value?.id, () => { redraw() })

const onResize = () => { redraw() }
window.addEventListener('resize', onResize)
window.addEventListener('layout-resize', onResize)
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  window.removeEventListener('layout-resize', onResize)
  if (analysisTimer) clearTimeout(analysisTimer)
})
</script>

<style scoped>
.home-simple {
  padding: 12px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  background: white;
  padding: 12px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.05);
}

.header h2 {
  margin: 0;
  color: #303133;
  font-size: 18px;
}

.header p {
  margin: 4px 0 0;
  color: #909399;
  font-size: 13px;
}

.content {
  max-width: 1400px;
  margin: 0 auto;
}

.chart-section {
  background: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.05);
}

.chart-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-title {
  font-weight: bold;
  font-size: 15px;
  color: #303133;
}

.chart-body {
  display: flex;
  gap: 48px;
  align-items: center;
}

.chart-canvas-wrap {
  width: 220px;
  height: 220px;
  flex-shrink: 0;
  position: relative;
}

.chart-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.chart-legend {
  flex: 1;
  min-width: 0;
}

.legend-row {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 8px;
}

.dot-protein { background: #67c23a; }
.dot-fat { background: #f56c6c; }
.dot-carbs { background: #e6a23c; }

.legend-val {
  margin-left: auto;
  font-weight: bold;
  color: #303133;
}

.legend-sub {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
  color: #909399;
  font-size: 12px;
  line-height: 1.8;
}

.plan-section {
  background: white;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.05);
}

.plan-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.plan-name {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.plan-meta {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.ai-analysis-section {
  margin-bottom: 16px;
}

.ai-analysis-card {
  background: #f0f7ff;
  border: 1px solid #d9ecff;
  border-radius: 8px;
  padding: 16px;
}

.ai-analysis-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.ai-title {
  font-weight: bold;
  color: #409eff;
  font-size: 15px;
}

.ai-analysis-content {
  background: white;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #e0eaf5;
}

.ai-text {
  margin: 0;
  white-space: pre-wrap;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.6;
  color: #606266;
}

/* 表格样式同步自 RecommendationView */
.csv-style-table {
  --el-table-header-bg-color: #f8f9fa;
  --el-table-row-hover-bg-color: #fdfdfd;
}

.csv-style-table :deep(th) {
  font-weight: 600;
  color: #444;
  height: 36px;
  padding: 4px 0;
}

.csv-style-table :deep(td) {
  padding: 0 !important;
}

.day-cell {
  padding: 6px 10px;
}

.day-cell-title {
  font-size: 16px;
  color: #409eff;
  margin-bottom: 2px;
  font-weight: 600;
}

.day-cell-date {
  background: #ffffff;
  padding: 2px 8px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  color: #909399;
  font-size: 12px;
}

.meal-cell-container {
  padding: 0;
  background: #fff;
  min-height: 80px;
}

.meal-dish-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.meal-dish-table th {
  background: #f0f2f5;
  font-size: 11px;
  padding: 6px 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.meal-dish-table td {
  padding: 8px 10px;
}

.category-td {
  background: #f9fafc !important;
  text-align: center;
  width: 100px;
}

.details-td {
  padding-left: 15px !important;
}

.meal-summary-td {
  background: #fdfdfd !important;
  border-top: 1px solid #f0f2f5;
  padding: 6px 12px !important;
}

.meal-total-energy {
  font-size: 11px;
  color: #909399;
  text-align: right;
  font-weight: 500;
}

.meal-total-energy span {
  color: #409eff;
  font-weight: 600;
  margin-left: 2px;
}

.dish-name-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.clickable-dish-name {
  font-size: 14px;
  color: #2c3e50;
  border-bottom: 1px dashed #dcdfe6;
  padding-bottom: 1px;
  cursor: pointer;
  transition: color 0.2s;
}

.clickable-dish-name:hover {
  color: #409eff;
  border-bottom-color: #409eff;
}

.dish-tags {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.servings-text {
  font-size: 11px;
  color: #909399;
  background: #f4f4f5;
  padding: 1px 4px;
  border-radius: 2px;
}

.dish-tooltip-content {
  max-width: 240px;
  padding: 4px;
}

.tooltip-section {
  margin-bottom: 8px;
}

.tooltip-section:last-child {
  margin-bottom: 0;
}

.tooltip-title {
  font-weight: bold;
  font-size: 12px;
  margin-bottom: 4px;
  color: #333;
}

.tooltip-text {
  font-size: 12px;
  line-height: 1.5;
  color: #666;
  white-space: pre-wrap;
}

.meal-empty {
  display: block;
  padding: 20px;
  text-align: center;
  color: #c0c4cc;
  font-size: 13px;
}

.procurement-section {
  margin-top: 24px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
}

.procurement-head {
  background: #f8f9fa;
  padding: 10px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: background 0.3s;
}

.procurement-head:hover {
  background: #f0f2f5;
}

.procurement-title {
  font-weight: bold;
  font-size: 14px;
  color: #303133;
}

.procurement-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.procurement-tip {
  font-size: 12px;
  color: #909399;
}

.empty-wrap {
  padding: 60px 0;
  background: white;
  border-radius: 8px;
}

@media (max-width: 768px) {
  .chart-body {
    flex-direction: column;
    gap: 16px;
  }
  
  .chart-canvas-wrap {
    width: 160px;
    height: 160px;
  }
}
</style>

<template>
  <div class="dish-management-container">
    <h2>菜品列表</h2>
    <p>管理您的早中晚菜品，支持添加、编辑、删除和发布</p>
    
    <div class="actions">
      <el-button type="primary" @click="$router.push('/add-dish')">添加菜品</el-button>
      <el-button @click="loadDishes">刷新</el-button>
    </div>
    
    <el-form inline style="margin-bottom: 12px;">
      <el-form-item label="餐次">
        <el-select v-model="filters.dish_type" placeholder="全部" style="width:100px">
          <el-option label="全部" value="" />
          <el-option label="早餐" value="早餐" />
          <el-option label="午餐" value="午餐" />
          <el-option label="晚餐" value="晚餐" />
        </el-select>
      </el-form-item>
      <el-form-item label="种类">
        <el-select
          v-model="filters.category"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="请选择种类"
          style="width:200px"
          clearable
        >
          <el-option
            v-for="item in categoryOptions"
            :key="item"
            :label="item"
            :value="item"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="口味">
        <el-input v-model="filters.flavor" placeholder="如：清淡" style="width:100px" />
      </el-form-item>
      <el-form-item label="关键字">
        <el-input v-model="filters.keyword" placeholder="名称/配方搜索" style="width:180px" />
      </el-form-item>
      <el-form-item label="包含食材">
        <el-input v-model="filters.ingredient" placeholder="搜索配方食材" style="width:160px" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
        <el-button type="info" link @click="showAdvanced = !showAdvanced">
          {{ showAdvanced ? '收起高级筛选' : '展开高级筛选' }}
          <el-icon>
            <ArrowUp v-if="showAdvanced" />
            <ArrowDown v-else />
          </el-icon>
        </el-button>
      </el-form-item>

      <div v-if="showAdvanced" style="margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 4px;">
        <div style="display: flex; flex-wrap: wrap; gap: 10px;">
          <el-form-item label="卡路里范围">
            <el-input-number v-model="filters.min_calories" :min="0" placeholder="最小" style="width:100px" :controls="false" />
            <span style="margin: 0 4px">-</span>
            <el-input-number v-model="filters.max_calories" :min="0" placeholder="最大" style="width:100px" :controls="false" />
          </el-form-item>
          <el-form-item label="蛋白质">
            <el-input-number v-model="filters.min_protein" :min="0" placeholder="最小" style="width:100px" :controls="false" />
            <span style="margin: 0 4px">-</span>
            <el-input-number v-model="filters.max_protein" :min="0" placeholder="最大" style="width:100px" :controls="false" />
          </el-form-item>
          <el-form-item label="碳水">
            <el-input-number v-model="filters.min_carbs" :min="0" placeholder="最小" style="width:100px" :controls="false" />
            <span style="margin: 0 4px">-</span>
            <el-input-number v-model="filters.max_carbs" :min="0" placeholder="最大" style="width:100px" :controls="false" />
          </el-form-item>
          <el-form-item label="脂肪">
            <el-input-number v-model="filters.min_fat" :min="0" placeholder="最小" style="width:100px" :controls="false" />
            <span style="margin: 0 4px">-</span>
            <el-input-number v-model="filters.max_fat" :min="0" placeholder="最大" style="width:100px" :controls="false" />
          </el-form-item>
          <el-form-item label="时令">
            <el-input v-model="filters.season" placeholder="如：夏季" style="width:120px" />
          </el-form-item>
        </div>
      </div>
    </el-form>
    
    <el-table
          v-loading="loading"
          :data="dishes"
          style="width: 100%"
          border
        >
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="dish_name" label="菜品名称" />
      <el-table-column prop="category" label="种类" width="120" />
      <el-table-column prop="dish_type" label="餐次类型" width="120">
        <template #default="scope">
          {{ dishTypeToText(scope.row.dish_type) }}
        </template>
      </el-table-column>
      <el-table-column prop="flavor" label="口味" width="120" />
      <el-table-column prop="season" label="时令" width="120" />
      <el-table-column label="创建时间" width="200">
        <template #default="scope">
          {{ formatLocalDate(scope.row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="scope">
          <el-button type="primary" size="small" @click="editDish(scope.row)">编辑</el-button>
          <el-button type="danger" size="small" :disabled="!isAdmin" @click="deleteDish(scope.row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <div class="pagination" v-if="total > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
    
    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
    >
      <el-form :model="dishForm" :rules="rules" ref="dishFormRef" label-width="120px">
        <el-form-item label="菜品名称" prop="dish_name">
          <el-input v-model="dishForm.dish_name" placeholder="请输入菜品名称" />
        </el-form-item>
        <el-form-item label="种类" prop="category">
          <el-select v-model="dishForm.category" placeholder="请选择种类" style="width: 100%">
            <el-option
              v-for="item in categoryOptions"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="菜品配方" prop="dish_recipe">
          <el-input v-model="dishForm.dish_recipe" type="textarea" rows="2" placeholder="请输入菜品配方" />
        </el-form-item>
        <el-form-item label="餐次类型" prop="dish_type">
          <el-select v-model="dishForm.dish_type" placeholder="请选择餐次类型">
            <el-option label="早餐" value="早餐" />
            <el-option label="午餐" value="午餐" />
            <el-option label="晚餐" value="晚餐" />
          </el-select>
        </el-form-item>
        <el-form-item label="口味" prop="flavor">
          <el-input v-model="dishForm.flavor" placeholder="请输入口味（可选）" />
        </el-form-item>
        <el-form-item label="时令" prop="season">
          <el-input v-model="dishForm.season" placeholder="请输入时令（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveDish">确定</el-button>
      </template>
    </el-dialog>
    
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, ArrowUp } from '@element-plus/icons-vue'
import { useRecommendationStore, useAuthStore } from '../stores/auth'
import { formatLocalDate } from '../utils/date'
import { useRoute } from 'vue-router'
import { dishTypeToText } from '../utils/constants'

// 定义菜品类型接口
interface Dish {
  id: number;
  dish_name: string;
  dish_recipe: string;
  dish_type: string;
  category: string;
  total_calories: number;
  total_carbohydrates: number;
  total_fat: number;
  total_protein: number;
  total_calcium: number;
  total_iron: number;
  total_vitamin_c: number;
  ingredient_count: number;
  matched_count: number;
  season: string;
  flavor: string;
  created_at?: string;
}

// 定义菜品表单类型
interface DishForm {
  id: number;
  dish_name: string;
  dish_recipe: string;
  dish_type: string;
  category: string;
  total_calories: number;
  total_carbohydrates: number;
  total_fat: number;
  total_protein: number;
  total_calcium: number;
  total_iron: number;
  total_vitamin_c: number;
  ingredient_count: number;
  matched_count: number;
  season: string;
  flavor: string;
}

const route = useRoute()

const recommendationStore = useRecommendationStore()
const authStore = useAuthStore()
const dishFormRef = ref<any>()

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

// 状态管理
const loading = ref(false)
const dialogVisible = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const dishes = ref<Dish[]>([])
const showAdvanced = ref(false)
const filters = reactive({
  dish_type: '',
  category: [] as string[],
  flavor: '',
  season: '',
  keyword: '',
  ingredient: '',
  min_calories: undefined as number | undefined,
  max_calories: undefined as number | undefined,
  min_protein: undefined as number | undefined,
  max_protein: undefined as number | undefined,
  min_carbs: undefined as number | undefined,
  max_carbs: undefined as number | undefined,
  min_fat: undefined as number | undefined,
  max_fat: undefined as number | undefined
})

// 对话框标题
const dialogTitle = computed(() => {
  return dishForm.id ? '编辑菜品' : '添加菜品'
})

const isAdmin = computed(() => (authStore.user?.role === 'admin'))

// 菜品表单
const dishForm = reactive<DishForm>({
  id: 0,
  dish_name: '',
  dish_recipe: '',
  dish_type: '',
  category: '',
  total_calories: 0,
  total_carbohydrates: 0,
  total_fat: 0,
  total_protein: 0,
  total_calcium: 0,
  total_iron: 0,
  total_vitamin_c: 0,
  ingredient_count: 0,
  matched_count: 0,
  season: '',
  flavor: ''
})

// 表单验证规则
const rules = reactive({
  dish_name: [
    { required: true, message: '请输入菜品名称', trigger: 'blur' },
    { min: 1, message: '菜品名称长度不能少于1个字符', trigger: 'blur' }
  ],
  dish_type: [
    { required: true, message: '请选择餐次类型', trigger: 'change' },
    { min: 1, message: '餐次类型长度不能少于1个字符', trigger: 'change' }
  ]
})

// 组件挂载时自动加载菜品数据
onMounted(async () => {
  await loadDishes()
})

// 监听路由变化，每次进入页面都重新获取数据
watch(
  () => route.path,
  async (newPath) => {
    if (newPath === '/dish-management') {
      console.log('路由切换到菜品管理页面，重新获取数据')
      await loadDishes()
    }
  },
  { immediate: true }
)

// 加载菜品列表
const loadDishes = async () => {
  try {
    loading.value = true
    console.log('开始加载菜品列表...')
    
    // 计算分页参数
    const skip = (currentPage.value - 1) * pageSize.value
    const limit = pageSize.value
    console.log('分页参数: skip=' + skip + ', limit=' + limit)
    
    let dishesData: any
    dishesData = await recommendationStore.listMenuItems(skip, limit, filters)
    console.log('获取到的菜品数据:', JSON.stringify(dishesData, null, 2))
    
    // 确保数据是数组，并转换为正确的Dish类型
    dishes.value = Array.isArray(dishesData) ? dishesData.map((item: any) => ({
      dish_name: item.dish_name || '',
      dish_recipe: item.dish_recipe || '',
      dish_type: dishTypeToText(item.dish_type || ''),
      category: item.category || '',
      total_calories: Number(item.total_calories ?? 0),
      total_carbohydrates: Number(item.total_carbohydrates ?? 0),
      total_fat: Number(item.total_fat ?? 0),
      total_protein: Number(item.total_protein ?? 0),
      total_calcium: Number(item.total_calcium ?? 0),
      total_iron: Number(item.total_iron ?? 0),
      total_vitamin_c: Number(item.total_vitamin_c ?? 0),
      ingredient_count: Number(item.ingredient_count ?? 0),
      matched_count: Number(item.matched_count ?? 0),
      season: item.season || '',
      flavor: item.flavor || '',
      id: Number(item.id ?? 0),
      created_at: item.created_at,
    })) : []
    
    const countData = await recommendationStore.countMenuItems(filters)
    total.value = Number((countData as any)?.total ?? dishes.value.length)
    const maxPage = Math.max(1, Math.ceil(total.value / pageSize.value))
    if (currentPage.value > maxPage) currentPage.value = 1
    console.log('菜品列表加载成功，共', total.value, '条菜品')
    
    // 只在非首次加载且有数据时显示成功消息，避免不必要的提示
    if (total.value > 0) {
      ElMessage.success('菜品列表加载成功，共' + total.value + '条菜品')
    }
  } catch (error: any) {
    console.error('加载菜品列表失败:', error)
    console.error('错误详情:', error.response?.data)
    console.error('错误状态码:', error.response?.status)
    
    const errorMsg = error.message || '未知错误'
    ElMessage.error(`加载菜品列表失败：${errorMsg}`)
    
    // 重置菜品列表为空白数组，确保UI显示正确
    dishes.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 取消管理员切换，统一显示全部

// 重置表单为初始状态
const resetDishForm = () => {
  Object.assign(dishForm, {
    id: 0,
    dish_name: '',
    dish_recipe: '',
    dish_type: '',
    category: '',
    total_calories: 0,
    total_carbohydrates: 0,
    total_fat: 0,
    total_protein: 0,
    total_calcium: 0,
    total_iron: 0,
    total_vitamin_c: 0,
    ingredient_count: 0,
    matched_count: 0,
    season: '',
    flavor: ''
  })
}

// 打开编辑对话框
const editDish = (row: Dish) => {
  console.log('编辑菜品:', row)
  
  // 填充表单数据，确保类型安全
  dishForm.id = Number(row.id) || 0
  dishForm.dish_name = row.dish_name || ''
  dishForm.dish_recipe = row.dish_recipe || ''
  dishForm.dish_type = row.dish_type || ''
  dishForm.category = row.category || ''
  dishForm.total_calories = Number(row.total_calories) || 0
  dishForm.total_carbohydrates = Number(row.total_carbohydrates) || 0
  dishForm.total_fat = Number(row.total_fat) || 0
  dishForm.total_protein = Number(row.total_protein) || 0
  dishForm.total_calcium = Number(row.total_calcium) || 0
  dishForm.total_iron = Number(row.total_iron) || 0
  dishForm.total_vitamin_c = Number(row.total_vitamin_c) || 0
  dishForm.ingredient_count = Number(row.ingredient_count) || 0
  dishForm.matched_count = Number(row.matched_count) || 0
  dishForm.season = row.season || ''
  dishForm.flavor = row.flavor || ''
  
  dialogVisible.value = true
}

// 准备请求数据
const prepareDishData = (): Partial<DishForm> => {
  return {
    dish_name: dishForm.dish_name,
    dish_recipe: dishForm.dish_recipe,
    dish_type: dishForm.dish_type,
    category: dishForm.category,
    total_calories: Number(dishForm.total_calories) || 0,
    total_carbohydrates: Number(dishForm.total_carbohydrates) || 0,
    total_fat: Number(dishForm.total_fat) || 0,
    total_protein: Number(dishForm.total_protein) || 0,
    total_calcium: Number(dishForm.total_calcium) || 0,
    total_iron: Number(dishForm.total_iron) || 0,
    total_vitamin_c: Number(dishForm.total_vitamin_c) || 0,
    ingredient_count: Number(dishForm.ingredient_count) || 0,
    matched_count: Number(dishForm.matched_count) || 0,
    season: dishForm.season || '',
    flavor: dishForm.flavor || ''
  }
}

// 保存菜品
const saveDish = async () => {
  if (!dishFormRef.value) {
    ElMessage.error('表单引用不存在')
    return
  }
  
  try {
    // DEBUG: 在验证前打印当前表单值，便于定位验证失败原因
    console.log('准备保存，当前表单值:', JSON.stringify(dishForm, null, 2))
    // 表单验证
    await dishFormRef.value.validate()
    console.log('表单验证通过，准备发送请求')
    
    // 准备请求数据
    const dishData = prepareDishData()
    console.log('请求数据:', JSON.stringify(dishData, null, 2))
    
    if (dishForm.id) {
      // 编辑菜品
      await recommendationStore.updateMenuItem(dishForm.id, dishData)
      ElMessage.success('菜品更新成功')
    } else {
      // 添加菜品
      await recommendationStore.createMenuItem(dishData)
      ElMessage.success('菜品添加成功')
    }
    
    // 关闭对话框并刷新数据
    dialogVisible.value = false
    loadDishes()
  } catch (error: any) {
    console.error('保存菜品失败:', error)
    console.error('错误响应:', error.response)
    console.error('错误响应数据:', error.response?.data)
    
    // 显示错误信息
    let errorMessage = '操作失败，请稍后重试'
    
    if (error.response?.data) {
      const data = error.response.data
      const status = error.response.status
      
      // 详细处理各种错误格式
      if (typeof data === 'string') {
        // 直接返回字符串错误
        errorMessage = data
      } else if (data.detail) {
        // 处理FastAPI的标准错误格式
        if (Array.isArray(data.detail)) {
          // 处理验证错误数组
          errorMessage = data.detail.map((err: any) => {
            const field = err.loc?.[1] || '未知字段'
            const msg = err.msg || '验证错误'
            return `${field}: ${msg}`
          }).join('\n')
        } else if (typeof data.detail === 'object') {
          // 处理对象类型的错误详情
          errorMessage = `${data.detail.error_type || ''}: ${data.detail.error_message || data.detail.message || '未知错误'}`
        } else {
          // 处理字符串类型的错误详情
          errorMessage = data.detail
        }
      } else if (data.error_message) {
        // 处理自定义的错误消息
        errorMessage = data.error_message
      } else if (data.message) {
        // 处理message字段
        errorMessage = data.message
      } else {
        // 尝试转换为字符串显示
        errorMessage = JSON.stringify(data)
      }
      
      // 添加状态码信息
      errorMessage = `(${status}) ${errorMessage}`
    } else if (error.message) {
      errorMessage = error.message
    }
    
    ElMessage.error(`操作失败：${errorMessage}`)
  }
}

// 删除菜品
const deleteDish = (row: Dish) => {
  ElMessageBox.confirm(
    `确定要删除菜品 "${row.dish_name}" 吗？`,
    '删除确认',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  )
  .then(async () => {
    try {
      await recommendationStore.deleteMenuItem(row.id)
      ElMessage.success('菜品删除成功')
      loadDishes()
    } catch (error: any) {
      const errorMsg = error.message || '未知错误'
      ElMessage.error(`删除失败：${errorMsg}`)
      console.error('删除失败:', error)
    }
  })
  .catch(() => {
    // 取消删除
  })
}

// 已移除发布状态切换（menu_items不包含发布字段）

// 分页相关
const handleSizeChange = (val: number) => {
  pageSize.value = val
  loadDishes()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  loadDishes()
}

const handleSearch = () => {
  currentPage.value = 1
  loadDishes()
}

const resetFilters = () => {
  Object.assign(filters, {
    dish_type: '',
    category: [],
    flavor: '',
    season: '',
    keyword: '',
    ingredient: '',
    min_calories: undefined,
    max_calories: undefined,
    min_protein: undefined,
    max_protein: undefined,
    min_carbs: undefined,
    max_carbs: undefined,
    min_fat: undefined,
    max_fat: undefined
  })
  handleSearch()
}

// 页面加载时加载菜品列表
onMounted(() => {
  loadDishes()
})
</script>

<style scoped>
.dish-management-container {
  padding: 20px;
  background-color: #fff;
  min-height: calc(100vh - 60px);
}

.dish-management-container h2 {
  margin-bottom: 10px;
  color: #303133;
}

.dish-management-container p {
  margin-bottom: 20px;
  color: #606266;
}

.actions {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}
</style>

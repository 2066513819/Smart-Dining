<template>
  <div class="ingredient-nutrition-container">
    <div class="header-section">
      <div>
        <h2>食材营养统计</h2>
        <p class="subtitle">管理食材的每100g营养成分信息，用于菜谱营养自动计算与分析</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="triggerFileUpload">导入营养表</el-button>
        <el-button type="primary" @click="handleAdd">新增食材</el-button>
        <el-button @click="fetchNutritions">刷新</el-button>
      </div>
    </div>

    <!-- 隐藏的文件上传输入 -->
    <input
      type="file"
      ref="fileInput"
      style="display: none"
      accept=".xlsx, .xls, .csv"
      @change="handleImport"
    />

    <div class="filter-section">
      <el-input
        v-model="searchQuery"
        placeholder="搜索食材名称..."
        style="width: 300px; margin-right: 12px"
        clearable
        @clear="fetchNutritions"
        @keyup.enter="fetchNutritions"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button type="primary" @click="fetchNutritions">查询</el-button>
      <el-button @click="resetFilters">重置</el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="nutritions"
      border
      stripe
      style="width: 100%; margin-top: 20px"
      max-height="650"
    >
      <el-table-column prop="name" label="食材名称" min-width="120" fixed="left" sortable />
      <el-table-column prop="energy_kj" label="能量(KJ)" width="100" sortable />
      <el-table-column prop="protein" label="蛋白质(g)" width="100" sortable />
      <el-table-column prop="fat" label="脂肪(g)" width="100" sortable />
      <el-table-column prop="carbohydrates" label="碳水(g)" width="100" sortable />
      <el-table-column prop="dietary_fiber" label="膳食纤维(g)" width="110" sortable />
      <el-table-column prop="vitamin_a" label="维A(mg)" width="90" sortable />
      <el-table-column prop="vitamin_c" label="维C(mg)" width="90" sortable />
      <el-table-column prop="calcium" label="钙(mg)" width="90" sortable />
      <el-table-column prop="iron" label="铁(mg)" width="90" sortable />
      <el-table-column prop="zinc" label="锌(mg)" width="90" sortable />
      <el-table-column prop="fat_energy_ratio" label="脂肪供能%" width="110" sortable />
      <el-table-column prop="carbohydrate_energy_ratio" label="碳水供能%" width="110" sortable />
      
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="scope">
          <el-button type="primary" size="small" @click="handleEdit(scope.row)">编辑</el-button>
          <el-popconfirm
            title="确定要删除这条营养记录吗？"
            @confirm="handleDelete(scope.row.id)"
          >
            <template #reference>
              <el-button type="danger" size="small">删除</el-button>
            </template>
          </el-popconfirm>
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

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑食材营养' : '新增食材营养'"
      width="650px"
    >
      <el-form :model="form" label-width="140px" ref="formRef" :rules="rules" class="nutrition-form">
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="食材名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入食材名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="能量(KJ)" prop="energy_kj">
              <el-input-number v-model="form.energy_kj" :precision="2" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="蛋白质(g)" prop="protein">
              <el-input-number v-model="form.protein" :precision="2" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="脂肪(g)" prop="fat">
              <el-input-number v-model="form.fat" :precision="2" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="碳水化合物(g)" prop="carbohydrates">
              <el-input-number v-model="form.carbohydrates" :precision="2" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="膳食纤维(g)" prop="dietary_fiber">
              <el-input-number v-model="form.dietary_fiber" :precision="2" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="维生素A(mg)" prop="vitamin_a">
              <el-input-number v-model="form.vitamin_a" :precision="4" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="维生素C(mg)" prop="vitamin_c">
              <el-input-number v-model="form.vitamin_c" :precision="2" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="钙(Ca)(mg)" prop="calcium">
              <el-input-number v-model="form.calcium" :precision="2" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="铁(Fe)(mg)" prop="iron">
              <el-input-number v-model="form.iron" :precision="2" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="锌(Zn)(mg)" prop="zinc">
              <el-input-number v-model="form.zinc" :precision="2" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="脂肪供能比(%)" prop="fat_energy_ratio">
              <el-input-number v-model="form.fat_energy_ratio" :precision="2" :min="0" :max="100" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="碳水供能比(%)" prop="carbohydrate_energy_ratio">
              <el-input-number v-model="form.carbohydrate_energy_ratio" :precision="2" :min="0" :max="100" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSave" :loading="saveLoading">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, Refresh, Search } from '@element-plus/icons-vue'
import { api } from '../stores/auth'
import * as XLSX from 'xlsx'

const loading = ref(false)
const saveLoading = ref(false)
const nutritions = ref([])
const searchQuery = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const formRef = ref()

// 分页相关
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const form = ref({
  id: null,
  name: '',
  energy_kj: 0,
  protein: 0,
  fat: 0,
  carbohydrates: 0,
  dietary_fiber: 0,
  vitamin_a: 0,
  vitamin_c: 0,
  calcium: 0,
  iron: 0,
  zinc: 0,
  fat_energy_ratio: 0,
  carbohydrate_energy_ratio: 0
})

const rules = {
  name: [{ required: true, message: '请输入食材名称', trigger: 'blur' }]
}

const fetchNutritions = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const limit = pageSize.value

    // 获取数据
    const data = await api.get('/ingredient_nutritions/', {
      params: { 
        name: searchQuery.value,
        skip,
        limit
      }
    })
    nutritions.value = data

    // 获取总数
    const countRes = await api.get('/ingredient_nutritions/count', {
      params: {
        name: searchQuery.value
      }
    })
    total.value = (countRes as any).total || 0
  } catch (err) {
    console.error('获取营养信息失败:', err)
    ElMessage.error('获取数据失败')
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchNutritions()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchNutritions()
}

const resetFilters = () => {
  searchQuery.value = ''
  currentPage.value = 1
  fetchNutritions()
}

const handleAdd = () => {
  isEdit.value = false
  form.value = {
    id: null,
    name: '',
    energy_kj: 0,
    protein: 0,
    fat: 0,
    carbohydrates: 0,
    dietary_fiber: 0,
    vitamin_a: 0,
    vitamin_c: 0,
    calcium: 0,
    iron: 0,
    zinc: 0,
    fat_energy_ratio: 0,
    carbohydrate_energy_ratio: 0
  }
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  isEdit.value = true
  form.value = { ...row }
  dialogVisible.value = true
}

const handleSave = async () => {
  saveLoading.value = true
  try {
    if (isEdit.value) {
      await api.put(`/ingredient_nutritions/${form.value.id}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await api.post('/ingredient_nutritions/', form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    fetchNutritions()
  } catch (err: any) {
    const detail = err.response?.data?.detail || '保存失败'
    ElMessage.error(detail)
  } finally {
    saveLoading.value = false
  }
}

const handleDelete = async (id: number) => {
  try {
    await api.delete(`/ingredient_nutritions/${id}`)
    ElMessage.success('删除成功')
    fetchNutritions()
  } catch (err) {
    ElMessage.error('删除失败')
  }
}

const triggerFileUpload = () => {
  fileInput.value?.click()
}

const handleImport = (e: Event) => {
  const files = (e.target as HTMLInputElement).files
  if (!files || files.length === 0) return
  
  const file = files[0]
  const reader = new FileReader()
  
  reader.onload = async (event) => {
    try {
      const data = new Uint8Array(event.target?.result as ArrayBuffer)
      const workbook = XLSX.read(data, { type: 'array' })
      const firstSheetName = workbook.SheetNames[0]
      const worksheet = workbook.Sheets[firstSheetName]
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 }) as any[][]
      
      // 这里的索引需要根据您的表格列名对齐
      // 食材名称 总膳食纤维 碳水化合物 维生素A 维生素C 能量 脂肪 蛋白质 钙 铁 锌 脂肪供能比 碳水供能比
      const items = []
      for (let i = 1; i < jsonData.length; i++) {
        const row = jsonData[i]
        if (row && row[0]) {
          items.push({
            name: String(row[0]).trim(),
            dietary_fiber: parseFloat(row[1]) || 0,
            carbohydrates: parseFloat(row[2]) || 0,
            vitamin_a: parseFloat(row[3]) || 0,
            vitamin_c: parseFloat(row[4]) || 0,
            energy_kj: parseFloat(row[5]) || 0,
            fat: parseFloat(row[6]) || 0,
            protein: parseFloat(row[7]) || 0,
            calcium: parseFloat(row[8]) || 0,
            iron: parseFloat(row[9]) || 0,
            zinc: parseFloat(row[10]) || 0,
            fat_energy_ratio: parseFloat(row[11]) || 0,
            carbohydrate_energy_ratio: parseFloat(row[12]) || 0
          })
        }
      }
      
      if (items.length === 0) {
        ElMessage.warning('未能从表格中识别到有效数据')
        return
      }

      console.log('Sending nutrition data:', { items })
      try {
        await api.post('/ingredient_nutritions/bulk-save', { items })
        ElMessage.success(`成功导入 ${items.length} 条营养数据`)
        fetchNutritions()
      } catch (postErr: any) {
        console.error('API Post Error:', postErr.response?.data || postErr.message)
        const detail = postErr.response?.data?.detail
        ElMessage.error(`导入失败: ${detail || '服务器响应错误'}`)
      }
    } catch (err: any) {
      console.error('导入失败:', err)
      ElMessage.error(`导入解析失败: ${err.message || '请检查文件格式'}`)
    } finally {
      if (fileInput.value) fileInput.value.value = ''
    }
  }
  
  reader.readAsArrayBuffer(file)
}

onMounted(() => {
  fetchNutritions()
})
</script>

<style scoped>
.ingredient-nutrition-container {
  padding: 20px;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-section h2 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.subtitle {
  margin: 8px 0 0;
  color: #606266;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filter-section {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.nutrition-form {
  padding-right: 20px;
}

:deep(.el-input-number .el-input__inner) {
  text-align: left;
}
</style>

<template>
  <div class="ingredient-cost-container">
    <div class="header-section">
      <div>
        <h2>食材成本管理</h2>
        <p class="subtitle">管理食材及配方的单价信息，用于菜谱成本自动计算</p>
      </div>
      <div class="header-actions">
        <el-upload
          ref="previewUploadRef"
          class="cost-table-upload"
          action="#"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handlePreviewCostTable"
          accept=".xlsx, .xls, .csv"
          style="display: none"
        />
        <el-button type="info" plain @click="triggerPreviewUpload">
          <el-icon style="margin-right: 4px;"><View /></el-icon>
          预览表格
        </el-button>
        <el-upload
          ref="importUploadRef"
          class="cost-table-upload"
          action="#"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="handleCostTableImport"
          accept=".xlsx, .xls, .csv"
          style="display: none"
        />
        <el-button type="primary" plain @click="triggerImportUpload">
          <el-icon style="margin-right: 4px;"><Upload /></el-icon>
          导入成本表格
        </el-button>
        <el-button type="primary" @click="handleAdd">新增食材</el-button>
        <el-button @click="fetchPrices">刷新</el-button>
      </div>
    </div>

    <!-- 价格表预览对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      title="价格表预览"
      width="800px"
      destroy-on-close
      class="preview-dialog"
    >
      <div v-if="previewData" class="preview-content">
        <div class="preview-summary">
          <el-descriptions :column="3" border>
            <el-descriptions-item label="文件名">{{ previewData.filename }}</el-descriptions-item>
            <el-descriptions-item label="总行数">{{ previewData.total_rows }} 行</el-descriptions-item>
            <el-descriptions-item label="已加载 Sheet" v-if="previewData.sheets_loaded?.length">
              {{ previewData.sheets_loaded.join('、') }}
            </el-descriptions-item>
            <el-descriptions-item label="列名识别">
              <el-tag v-if="previewData.required_columns_found.l1_category" type="success" size="small">一级分类 ✓</el-tag>
              <el-tag v-else type="danger" size="small">一级分类 ✗</el-tag>
              <el-tag v-if="previewData.required_columns_found.ingredient_name" type="success" size="small" style="margin-left: 8px;">食材名称 ✓</el-tag>
              <el-tag v-else type="danger" size="small" style="margin-left: 8px;">食材名称 ✗</el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>
        <div class="preview-columns" style="margin-top: 16px;">
          <h4>列名映射检测：</h4>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item
              v-for="(col, field) in previewData.columns_detected"
              :key="field"
              :label="field"
            >
              <span v-if="col" style="color: #67c23a;">{{ col }} ✓</span>
              <span v-else style="color: #f56c6c;">未检测到</span>
            </el-descriptions-item>
          </el-descriptions>
        </div>
        <div class="preview-data" style="margin-top: 16px;">
          <h4>数据预览（前10行）：</h4>
          <el-table :data="previewData.preview" style="width: 100%" size="small" max-height="400">
            <el-table-column prop="row" label="行号" width="60" />
            <el-table-column label="原始数据">
              <template #default="scope">
                <div class="raw-data" style="font-size: 12px; color: #666;">
                  {{ JSON.stringify(scope.row.raw).slice(0, 100) }}{{ JSON.stringify(scope.row.raw).length > 100 ? '...' : '' }}
                </div>
              </template>
            </el-table-column>
            <el-table-column label="解析结果">
              <template #default="scope">
                <div v-if="scope.row.parsed" class="parsed-data" style="font-size: 12px;">
                  <div><strong>分类:</strong> {{ scope.row.parsed.l1_name }}<span v-if="scope.row.parsed.l2_name"> / {{ scope.row.parsed.l2_name }}</span></div>
                  <div><strong>食材:</strong> {{ scope.row.parsed.ingredient_name }}</div>
                  <div><strong>价格:</strong> {{ scope.row.parsed.price }} 元/{{ scope.row.parsed.unit }}</div>
                </div>
                <div v-else style="color: #f56c6c; font-size: 12px;">数据不完整，跳过</div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button @click="previewDialogVisible = false">关闭</el-button>
        <el-button
          type="primary"
          @click="previewDialogVisible = false; triggerImportUpload()"
          :disabled="!previewData?.required_columns_found?.l1_category || !previewData?.required_columns_found?.ingredient_name"
        >
          确认并导入
        </el-button>
      </template>
    </el-dialog>

    <div class="filter-section">
      <el-input
        v-model="searchQuery"
        placeholder="搜索食材或配方名称..."
        style="width: 300px; margin-right: 12px"
        clearable
        @clear="fetchPrices"
        @keyup.enter="fetchPrices"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button type="primary" @click="fetchPrices">查询</el-button>
      <el-button @click="resetFilters">重置</el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="prices"
      border
      stripe
      style="width: 100%; margin-top: 20px"
    >
      <el-table-column prop="name" label="食材/配方名称" min-width="180" sortable />
      <el-table-column prop="price" label="单价" width="150" sortable>
        <template #default="scope">
          <span class="price-text">¥ {{ formatPrice(scope.row.price) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="unit" label="单位" width="100" />
      <el-table-column prop="updated_at" label="最后更新" width="180">
        <template #default="scope">
          {{ formatDate(scope.row.updated_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="scope">
          <el-button type="primary" size="small" @click="handleEdit(scope.row)">编辑</el-button>
          <el-popconfirm
            title="确定要删除这条价格记录吗？"
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
      :title="isEdit ? '编辑食材价格' : '新增食材价格'"
      width="400px"
    >
      <el-form :model="form" label-width="100px" ref="formRef" :rules="rules">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入食材或配方名称" />
        </el-form-item>
        <el-form-item label="单价" prop="price">
          <el-input-number
            v-model="form.price"
            :precision="4"
            :step="0.1"
            :min="0"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="单位" prop="unit">
          <el-select v-model="form.unit" placeholder="选择单位" style="width: 100%">
            <el-option label="500g" value="500g" />
            <el-option label="斤" value="斤" />
            <el-option label="g" value="g" />
            <el-option label="kg" value="kg" />
            <el-option label="个" value="个" />
            <el-option label="ml" value="ml" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElLoading, type UploadFile } from 'element-plus'
import { Search, Plus, Refresh, Upload, View } from '@element-plus/icons-vue'
import { api } from '../stores/auth'

interface IngredientPrice {
  id?: number
  name: string
  price: number
  unit: string
  updated_at?: string
}

const loading = ref(false)
const submitting = ref(false)
const prices = ref<IngredientPrice[]>([])
const searchQuery = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const previewUploadRef = ref<any>(null)
const importUploadRef = ref<any>(null)
const previewData = ref<any>(null)
const previewDialogVisible = ref(false)

// 分页相关
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const form = ref<IngredientPrice>({
  name: '',
  price: 0,
  unit: '500g'
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  price: [{ required: true, message: '请输入单价', trigger: 'blur' }],
  unit: [{ required: true, message: '请输入单位', trigger: 'blur' }]
}

const fetchPrices = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const limit = pageSize.value
    
    // 获取数据
    const data = await api.get('/ingredient_prices/my-prices', {
      params: {
        name: searchQuery.value,
        skip,
        limit
      }
    })
    prices.value = data as IngredientPrice[]
    
    // 获取总数
    const countRes = await api.get('/ingredient_prices/count', {
      params: {
        name: searchQuery.value
      }
    })
    total.value = (countRes as any).total || 0
  } catch (err) {
    console.error('Fetch prices error:', err)
    ElMessage.error('获取食材价格失败')
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  fetchPrices()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  fetchPrices()
}

const resetFilters = () => {
  searchQuery.value = ''
  currentPage.value = 1
  fetchPrices()
}

const triggerPreviewUpload = () => {
  previewUploadRef.value?.$el?.querySelector('input')?.click()
}

const triggerImportUpload = () => {
  importUploadRef.value?.$el?.querySelector('input')?.click()
}

const handlePreviewCostTable = async (file: UploadFile) => {
  if (!file.raw) {
    ElMessage.warning('请选择文件')
    return
  }
  const loading = ElLoading.service({
    lock: true,
    text: '正在分析表格结构...',
    background: 'rgba(0, 0, 0, 0.7)'
  })
  try {
    const formData = new FormData()
    formData.append('file', file.raw)
    formData.append('rows', '10')
    const result = await api.post('/supplier-price-import/preview-supplier-prices', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    loading.close()
    if (result) {
      previewData.value = result
      previewDialogVisible.value = true
      if (!result.required_columns_found?.l1_category) {
        ElMessage.warning('未检测到"一级分类"列，请检查表格列名')
      } else if (!result.required_columns_found?.ingredient_name) {
        ElMessage.warning('未检测到"食材名称"列，请检查表格列名')
      } else {
        ElMessage.success(`表格分析完成！共 ${result.total_rows} 行数据，列名识别成功`)
      }
    }
  } catch (err: any) {
    loading.close()
    const errorMsg = err.response?.data?.detail || '预览失败，请检查文件格式'
    ElMessage.error(errorMsg)
  }
  previewUploadRef.value?.clearFiles?.()
}

const handleCostTableImport = async (file: UploadFile) => {
  if (!file.raw) {
    ElMessage.warning('请选择文件')
    return
  }
  const loading = ElLoading.service({
    lock: true,
    text: '正在导入供应商价格表...',
    background: 'rgba(0, 0, 0, 0.7)'
  })
  try {
    const formData = new FormData()
    formData.append('file', file.raw)
    const result = await api.post('/supplier-price-import/import-supplier-prices', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    loading.close()
    if (result && result.success) {
      const stats = result.stats
      ElMessage.success(
        `导入成功！共处理 ${stats.total} 条，成功导入 ${stats.success} 条，` +
        `新建一级分类 ${stats.l1_created} 个，二级分类 ${stats.l2_created} 个`
      )
      fetchPrices()
      if (result.columns_detected?.price) {
        ElMessage.info('已自动提取价格信息')
      }
    } else {
      ElMessage.warning(result?.message || '导入完成，但可能有部分数据未处理')
    }
    if (result?.stats?.errors?.length) {
      const errors = result.stats.errors
      if (errors.length <= 3) {
        errors.forEach((err: string) => ElMessage.error(err))
      } else {
        ElMessage.error(`有 ${errors.length} 条数据导入失败，请检查数据格式`)
      }
    }
  } catch (err: any) {
    loading.close()
    const errorMsg = err.response?.data?.detail || err.message || '导入失败'
    ElMessage.error(errorMsg)
    if (err.response?.status === 400 || err.response?.data?.detail?.includes?.('未找到')) {
      ElMessage.info('支持的列名：一级分类、食材名称/商品名、入库单价、基本单位、商品备注等')
    }
  }
  importUploadRef.value?.clearFiles?.()
}

const handleAdd = () => {
  isEdit.value = false
  form.value = { name: '', price: 0, unit: 'g' }
  dialogVisible.value = true
}

const handleEdit = (row: IngredientPrice) => {
  isEdit.value = true
  form.value = { ...row }
  dialogVisible.value = true
}

const handleDelete = async (id: number) => {
  try {
    await api.delete(`/ingredient_prices/${id}`)
    ElMessage.success('删除成功')
    fetchPrices()
  } catch (err) {
    ElMessage.error('删除失败')
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      submitting.value = true
      try {
        if (isEdit.value) {
          await api.put(`/ingredient_prices/${form.value.id}`, form.value)
        } else {
          await api.post('/ingredient_prices/', form.value)
        }
        ElMessage.success(isEdit.value ? '修改成功' : '添加成功')
        dialogVisible.value = false
        fetchPrices()
      } catch (err) {
        ElMessage.error('保存失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

const formatPrice = (val: number) => {
  return Number(val).toFixed(4)
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

onMounted(() => {
  console.log('IngredientCostView mounted')
  fetchPrices()
})
</script>

<style scoped>
.ingredient-cost-container {
  padding: 24px;
  background-color: #fff;
  border-radius: 8px;
  min-height: calc(100vh - 120px);
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-section h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #303133;
}

.subtitle {
  margin: 0;
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

.price-text {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace;
  font-weight: 600;
  color: #f56c6c;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

:deep(.el-table .cell) {
  white-space: nowrap;
}
</style>

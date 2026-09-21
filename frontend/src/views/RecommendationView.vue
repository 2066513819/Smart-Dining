<template>
  <div class="recommendation-container">
    <main class="main-content">
      <!-- 菜品搜索弹窗 -->
      <el-dialog
        v-model="searchDishVisible"
        title="从菜品库添加"
        width="550px"
        destroy-on-close
        class="search-dish-dialog"
      >
        <div class="search-tip" style="margin-bottom: 20px; color: #909399; font-size: 13px; display: flex; align-items: center; gap: 4px; background: #f8f9fa; padding: 10px; border-radius: 4px;">
          <el-icon><InfoFilled /></el-icon>
          <span>输入菜品关键词，从已有菜品库中选择并添加到当前餐次。</span>
        </div>
        
        <el-form label-width="80px">
          <el-form-item label="搜索菜品">
            <el-select
              v-model="selectedSearchDish"
              filterable
              remote
              reserve-keyword
              placeholder="输入菜品名称，如：宫保鸡丁"
              :remote-method="searchDishesFromDB"
              :loading="searchLoading"
              style="width: 100%"
              value-key="id"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
              <el-option
                v-for="item in dbSearchResult"
                :key="item.id"
                :label="item.dish_name"
                :value="item"
                class="dish-search-option"
              >
                <div class="search-item-content">
                  <div class="search-item-left">
                    <span class="search-item-name">{{ item.dish_name }}</span>
                    <el-tag size="small" type="warning" plain v-if="item.category" class="search-item-tag">{{ item.category }}</el-tag>
                    <el-tag size="small" type="info" plain class="search-item-tag">{{ item.flavor || '原味' }}</el-tag>
                  </div>
                  <div class="search-item-right">
                    <el-tag size="small" :type="item.dish_type === 'breakfast' ? 'success' : (item.dish_type === 'lunch' ? 'warning' : 'danger')" effect="light">
                      {{ dishTypeToText(item.dish_type) }}
                    </el-tag>
                    <span class="search-item-calories">{{ item.total_calories }} kcal</span>
                  </div>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="searchDishVisible = false">取消</el-button>
            <el-button type="primary" @click="confirmAddDishToMeal" :disabled="!selectedSearchDish" class="confirm-add-btn">
              确认添加
            </el-button>
          </span>
        </template>
      </el-dialog>

      <el-dialog
        v-model="customDateDialogVisible"
        title="选择应用日期"
        width="520px"
        destroy-on-close
        class="custom-date-dialog"
      >
        <div class="custom-date-tip">
          默认从明天开始，可选择本月任意日期（可不连续）。
        </div>
        <div class="custom-date-calendar">
          <el-calendar v-model="calendarValue">
            <template #date-cell="{ data }">
              <div
                class="calendar-cell"
                :class="{
                  selected: customDatesSet.has(data.day),
                  disabled: isCustomDateDisabled(data.date)
                }"
                @click="toggleCustomDate(data.day, data.date)"
              >
                <span class="calendar-cell-day">{{ data.day.split('-')[2] }}</span>
              </div>
            </template>
          </el-calendar>
        </div>
        <div class="custom-date-selected">
          <span class="selected-label">已选：</span>
          <span v-if="customDatesDraft.length === 0" class="selected-empty">未选择</span>
          <el-tag
            v-else
            v-for="d in customDatesDraft"
            :key="d"
            size="small"
            closable
            @close="removeCustomDate(d)"
            style="margin: 0 6px 6px 0;"
          >
            {{ d }}
          </el-tag>
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="cancelCustomDateDialog">取消</el-button>
            <el-button type="primary" @click="confirmCustomDateDialog">确定</el-button>
          </span>
        </template>
      </el-dialog>

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
          <span class="dialog-footer">
            <el-button @click="previewDialogVisible = false">关闭</el-button>
            <el-button
              type="primary"
              @click="previewDialogVisible = false; triggerImportUpload()"
              :disabled="!previewData?.required_columns_found?.l1_category || !previewData?.required_columns_found?.ingredient_name"
            >
              确认并导入
            </el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 页面标题 -->
      <section class="page-header">
        <div class="header-content">
          <div class="title-section">
            <div style="display: flex; align-items: center; gap: 12px;">
              <h2>菜谱制定</h2>
              <el-tag v-if="adminDiningStyle === '团餐'" type="danger" effect="dark" size="large" style="border-radius: 4px; font-weight: bold;">
                团餐模式
              </el-tag>
              <el-tag v-else type="success" effect="plain" size="large" style="border-radius: 4px;">
                盘餐模式
              </el-tag>
            </div>
            <p class="subtitle">
              {{ adminDiningStyle === '团餐' ? '当前处于团餐模式：品类丰富，自助配餐，份量已自动上浮 15%' : '根据数据库菜品信息，结合您的选择生成个性化菜谱' }}
            </p>
          </div>
        </div>
      </section>

      <!-- 添加已有食材 -->
      <section class="custom-dishes-section">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <h3>添加已有食材</h3>
          <div style="display: flex; gap: 8px;">
            <el-upload
              ref="previewUploadRef"
              class="cost-table-upload"
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handlePreviewCostTable"
              accept=".xlsx, .xls, .csv"
              style="display: none"
            >
              <el-button type="info" plain>
                <el-icon style="margin-right: 4px;"><View /></el-icon>
                预览
              </el-button>
            </el-upload>
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
            >
              <el-button type="success" plain>
                <el-icon style="margin-right: 4px;"><Upload /></el-icon>
                导入成本表格
              </el-button>
            </el-upload>
            <el-button type="success" plain @click="triggerImportUpload">
              <el-icon style="margin-right: 4px;"><Upload /></el-icon>
              导入成本表格
            </el-button>
          </div>
        </div>
        <div class="custom-dishes-container">
          <div style="display:flex;gap:12px;align-items:center;margin-bottom:12px;">
            <el-input v-model="ingredientInput" placeholder="请输入食材，如：鸡蛋、菠菜" style="max-width:360px;" />
            <el-button type="primary" @click="addIngredient">
              <el-icon style="margin-right: 4px;"><Plus /></el-icon>
              添加
            </el-button>
          </div>
          <div v-if="importedFileName" style="display: flex; align-items: center; gap: 8px;">
            <el-tag type="success" closable @close="clearImportedFile" size="large">
              <el-icon style="margin-right: 4px;"><Document /></el-icon>
              已导入价格表: {{ importedFileName }}
            </el-tag>
            <span style="font-size: 13px; color: #909399;">已加载 {{ ingredientPriceEntryCount }} 条价格数据</span>
          </div>
          <div v-else-if="availableIngredients.length > 0" style="display:flex;flex-wrap:wrap;gap:8px;">
            <el-tag
              v-for="(ing, i) in availableIngredients"
              :key="ing + i"
              type="info"
              closable
              @close="removeIngredient(i)"
            >
              {{ ing }}
            </el-tag>
          </div>
        </div>
      </section>

      <!-- 规则选择区域 -->
      <section class="rules-section">
        <h3>推荐规则</h3>
        <el-form :model="rulesForm" label-position="top" class="rules-form">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="餐饮类型（多选）">
                <el-select 
                  v-model="rulesForm.dishType" 
                  placeholder="请选择餐饮类型" 
                  clearable
                  multiple
                >
                  <el-option label="早餐" value="早餐"></el-option>
                  <el-option label="午餐" value="午餐"></el-option>
                  <el-option label="晚餐" value="晚餐"></el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="口味（多选）">
                <el-select 
                  v-model="rulesForm.flavor" 
                  placeholder="请选择口味" 
                  clearable
                  multiple
                >
                  <el-option label="原味" value="原味"></el-option>
                  <el-option label="甜" value="甜"></el-option>
                  <el-option label="咸" value="咸"></el-option>
                  <el-option label="辣" value="辣"></el-option>
                  <el-option label="酸" value="酸"></el-option>
                  <el-option label="腥" value="腥"></el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="时令">
                <el-select 
                  v-model="rulesForm.season" 
                  placeholder="请选择时令" 
                  multiple
                  clearable
                >
                  <el-option label="四季皆宜" value="四季皆宜"></el-option>
                  <el-option label="春季" value="春季"></el-option>
                  <el-option label="夏季" value="夏季"></el-option>
                  <el-option label="秋季" value="秋季"></el-option>
                  <el-option label="冬季" value="冬季"></el-option>
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="天数">
                <el-input-number 
                  v-model="rulesForm.days" 
                  :min="1" 
                  :max="7" 
                  :step="1" 
                  :disabled="dateMode === 'custom'"
                  placeholder="请输入天数"
                ></el-input-number>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="份数">
                <el-input-number 
                  v-model="rulesForm.servings" 
                  :min="1" 
                  :max="100" 
                  :step="1" 
                  placeholder="请输入份数"
                ></el-input-number>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="默认人群">
                <el-select 
                  v-model="rulesForm.target_age_group" 
                  placeholder="默认目标人群" 
                  clearable
                >
                  <el-option label="小学 (6-11岁)" value="primary"></el-option>
                  <el-option label="初中 (12-14岁)" value="junior_low"></el-option>
                  <el-option label="高中 (15-17岁)" value="senior"></el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <!-- 分餐次人群设置已由管理员规则统一配置，页面不再提供该项 -->
            <el-col :span="8">
              <el-form-item label="营养需求（可选）">
                <el-checkbox-group v-model="rulesForm.nutritionRequirements">
                  <el-checkbox label="高蛋白" border size="small"></el-checkbox>
                  <el-checkbox label="低脂肪" border size="small"></el-checkbox>
                  <el-checkbox label="低碳水" border size="small"></el-checkbox>
                </el-checkbox-group>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="应用日期">
                <div class="date-mode-row">
                  <el-radio-group v-model="dateMode" size="small">
                    <el-radio-button label="continuous">连续</el-radio-button>
                    <el-radio-button label="custom">自选</el-radio-button>
                  </el-radio-group>

                  <div v-if="dateMode === 'continuous'" class="date-mode-detail">
                    <span class="date-mode-label">开始日期：</span>
                    <el-date-picker
                      v-model="startDate"
                      type="date"
                      format="YYYY-MM-DD"
                      value-format="YYYY-MM-DD"
                      :clearable="false"
                      :disabled-date="disableStartDate"
                    />
                    <span class="date-preview">
                      默认从 {{ tomorrowYMD }} 开始，连续 {{ rulesForm.days }} 天
                    </span>
                  </div>

                  <div v-else class="date-mode-detail">
                    <el-button type="primary" plain @click="openCustomDateDialog">
                      选择日期
                    </el-button>
                    <span class="date-preview">
                      已选 {{ customDates.length }} 天（默认从 {{ tomorrowYMD }} 开始）
                    </span>
                  </div>
                </div>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-row>
            <el-col :span="24" class="form-actions">
              <el-button 
                type="primary" 
                @click="generateRecipePlan" 
                :loading="recStore.loading"
                size="large"
              >
                {{ recStore.loading ? '生成中...' : '生成菜谱计划' }}
              </el-button>
              <el-button 
                @click="resetRules"
                size="large"
              >
                重置规则
              </el-button>
            </el-col>
          </el-row>
        </el-form>
      </section>

      <!-- 加载状态 -->
      <div class="loading-container" v-if="recStore.loading">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <p>正在生成菜谱计划，请稍候...</p>
        <div class="loading-progress-wrapper" v-if="loadingProgress > 0">
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

      <!-- 错误信息 -->
      <div class="error-container" v-if="recStore.error">
        <el-alert
          title="错误"
          :description="recStore.error"
          type="error"
          show-icon
          :closable="false"
        >
          <template #default>
            <el-button size="small" type="primary" @click="generateRecipePlan">重试</el-button>
          </template>
        </el-alert>
      </div>

      <!-- 菜谱计划结果 -->
      <section class="results-section" v-else-if="displayDishes.length > 0">
        <h3>菜谱计划</h3>
        <div class="plan-actions" style="margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between;">
          <div>
            <el-button 
              type="success" 
              @click="savePlan"
              size="large"
            >
              保存菜谱计划
            </el-button>
            <el-button 
              type="primary" 
              @click="publishPlan"
              size="large"
              style="margin-left: 16px;"
            >
              发布菜谱计划
            </el-button>
          </div>
          <div class="total-cost-display" style="font-size: 18px; font-weight: bold; color: #f56c6c;">
            预计总成本：¥{{ totalPlanCost }}
          </div>
        </div>
        
        <div class="recipe-plan-table horizontal-layout">
          <el-table
            :data="flattenedRows"
            :span-method="objectSpanMethod"
            border
            style="width: 100%"
            class="csv-style-table"
          >
            <!-- 1. 时间列 -->
            <el-table-column
              label="时间"
              width="120"
              align="center"
            >
              <template #default="scope">
                <div class="day-cell">
                  <div class="day-cell-title">第{{ scope.row.day }}天</div>
                  <div v-if="scope.row.apply_date" class="day-cell-date">
                    {{ formatApplyDate(scope.row.apply_date) }}
                  </div>
                </div>
              </template>
            </el-table-column>

            <!-- 2. 餐饮类型列 -->
            <el-table-column
              label="餐饮"
              width="100"
              align="center"
            >
              <template #default="scope">
                <div class="meal-type-cell">
                  <div class="meal-type-name">{{ scope.row.mealType }}</div>
                </div>
              </template>
            </el-table-column>

            <!-- 3. 菜品类型列 -->
            <el-table-column
              label="类型"
              width="100"
              align="center"
            >
              <template #default="scope">
                <template v-if="!scope.row.isPlaceholder">
                  <el-tag size="small" type="warning" effect="light" v-if="scope.row.dish.category">
                    {{ scope.row.dish.category }}
                  </el-tag>
                  <el-tag size="small" type="success" effect="light" v-else-if="scope.row.dish.dish_type">
                    {{ dishTypeToText(scope.row.dish.dish_type) }}
                  </el-tag>
                  <span v-else>-</span>
                </template>
                <span v-else>-</span>
              </template>
            </el-table-column>

            <!-- 4. 菜品详情列 -->
            <el-table-column
              label="菜品详情"
              min-width="250"
            >
              <template #default="scope">
                <div v-if="!scope.row.isPlaceholder" class="dish-detail-horizontal">
                  <div class="dish-name-row">
                    <el-tooltip placement="top" effect="light">
                      <template #content>
                        <div class="dish-tooltip-content">
                          <div class="tooltip-section">
                            <div class="tooltip-title">配方/描述：</div>
                            <div class="tooltip-text">{{ cleanDescription(scope.row.dish.description) || '暂无描述' }}</div>
                          </div>
                          <div class="tooltip-section">
                            <div class="tooltip-title">营养指标：</div>
                            <div v-if="adminDiningStyle === '团餐'" class="tooltip-text" style="color: #e6a23c; font-style: italic; margin-bottom: 8px; border-bottom: 1px dashed #e6a23c; padding-bottom: 4px;">
                              团餐提示：此处为单份参考。整体营养达标情况请查看“营养评估(平均)”列。
                            </div>
                            <div class="tooltip-text">{{ scope.row.dish.nutrition }}</div>
                          </div>
                        </div>
                      </template>
                      <span class="clickable-dish-name">{{ scope.row.dish.name }}</span>
                    </el-tooltip>
                    <span class="dish-tags">
                      <span class="servings-text">{{ scope.row.dish.servings }}份</span>
                      <el-tag size="small" type="info" effect="plain">{{ scope.row.dish.flavor || '原味' }}</el-tag>
                      <span v-if="scope.row.dish.cost_price" class="cost-text" style="font-size: 12px; color: #f56c6c; font-weight: bold; margin-left: 8px;">¥{{ scope.row.dish.cost_price }}</span>
                    </span>
                  </div>
                </div>
                <div v-else class="empty-placeholder">
                  <span class="empty-text">暂无菜品</span>
                </div>
              </template>
            </el-table-column>

            <!-- 5. 营养达标列 (仅团餐模式显示) -->
            <el-table-column
              v-if="adminDiningStyle === '团餐'"
              label="营养评估(平均)"
              width="180"
              align="center"
            >
              <template #default="scope">
                <div v-if="scope.row.summary" class="nutrition-summary-cell">
                  <el-tag :type="getSummaryTagType(scope.row.summary)" effect="dark" size="small">
                    {{ getSummaryTagText(scope.row.summary) }}
                  </el-tag>
                  <el-popover placement="left" :width="320" trigger="hover">
                    <template #reference>
                      <div class="summary-preview clickable" style="margin-top: 8px; font-size: 12px; color: #409eff;">
                        查看平均营养详情
                      </div>
                    </template>
                    <div class="nutrition-details">
                      <div class="details-title" style="font-weight: bold; margin-bottom: 6px; border-bottom: 1px solid #eee; padding-bottom: 5px; display: flex; justify-content: space-between; align-items: center;">
                        <span>平均每人摄入 ({{ scope.row.summary.num_people || 1 }}人)</span>
                        <span v-if="scope.row.summary.avg_cost" style="color: #f56c6c; font-size: 14px;">¥{{ scope.row.summary.avg_cost.toFixed(2) }}</span>
                      </div>
                      <div v-if="scope.row.summary.target_age_group" class="target-info" style="font-size: 12px; color: #e6a23c; margin-bottom: 10px;">
                        目标人群: {{ scope.row.summary.target_age_group === 'primary' ? '小学' : (['junior_low', 'junior_high'].includes(scope.row.summary.target_age_group) ? '初中' : '高中') }}
                      </div>
                      <template v-if="isWeightedSummary(scope.row.summary)">
                        <div class="detail-item" style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 13px;">
                          <span class="detail-label">综合评分:</span>
                          <div class="detail-values" style="color: #409eff; font-weight: bold;">
                            {{ toScore(scope.row.summary.weighted_score).toFixed(2) }}/100
                          </div>
                        </div>
                        <div class="detail-item" style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 13px;">
                          <span class="detail-label">营养评分:</span>
                          <div class="detail-values" style="color: #67c23a; font-weight: bold;">
                            {{ toScore(scope.row.summary.nutrition_score).toFixed(2) }}/100
                          </div>
                        </div>
                        <div class="detail-item" style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 13px;">
                          <span class="detail-label">成本评分:</span>
                          <div class="detail-values" style="color: #e6a23c; font-weight: bold;">
                            {{ toScore(scope.row.summary.cost_score).toFixed(2) }}/100
                          </div>
                        </div>
                        <div class="detail-item" style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 13px;">
                          <span class="detail-label">多样性评分:</span>
                          <div class="detail-values" style="color: #909399; font-weight: bold;">
                            {{ toScore(scope.row.summary.variety_score).toFixed(2) }}/100
                          </div>
                        </div>
                      </template>
                      <template v-else>
                        <div
                          v-for="(detail, key) in (scope.row.summary.compliance_details || {})"
                          :key="key"
                          class="detail-item"
                          style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 13px;"
                        >
                          <span class="detail-label">{{ getNutrientName(key) }}:</span>
                          <div class="detail-values-wrapper" style="text-align: right;">
                            <div class="detail-values" :style="{ color: detail.status ? '#67c23a' : '#f56c6c', fontWeight: 'bold' }">
                              {{ detail.actual.toFixed(1) }} / {{ detail.target.toFixed(1) }}
                            </div>
                            <div v-if="!detail.status && detail.min !== undefined" class="compliance-range" style="font-size: 10px; color: #909399;">
                              范围: {{ detail.min.toFixed(1) }}{{ (detail.max && detail.max !== Infinity) ? '-' + detail.max.toFixed(1) : '+' }}
                            </div>
                          </div>
                        </div>
                        <div
                          v-if="!scope.row.summary.compliance_details || Object.keys(scope.row.summary.compliance_details).length === 0"
                          style="font-size: 12px; color: #909399;"
                        >
                          暂无可展示的营养明细（该餐次可能返回的是评分摘要）。
                        </div>
                      </template>
                      <div class="detail-tip" style="margin-top: 10px; font-size: 11px; color: #909399; font-style: italic; border-top: 1px dashed #eee; padding-top: 5px;">
                        {{ isWeightedSummary(scope.row.summary) ? '注：当前为加权评分说明（营养40%+成本35%+多样性25%）。' : '注：能量与三大营养素允许 ±15% 波动，微量元素需达到 90% 以上。' }}
                      </div>
                    </div>
                  </el-popover>
                </div>
                <div v-else class="empty-text">-</div>
              </template>
            </el-table-column>

            <!-- 6. 餐次管理 -->
            <el-table-column
              label="餐次管理"
              width="140"
              align="center"
            >
              <template #default="scope">
                <div class="meal-actions-vertical">
                  <el-button size="small" plain class="meal-manage-btn meal-btn-edit" @click="openMealEdit(scope.row.day, scope.row.mealType)">
                    修改
                  </el-button>
                  <el-button size="small" plain class="meal-manage-btn meal-btn-add" @click="openAddDishSearch(scope.row.day, scope.row.mealType)">
                    <el-icon><Plus /></el-icon>添加
                  </el-button>
                  <el-button size="small" plain class="meal-manage-btn meal-btn-regen" @click="regenerateMeal(scope.row.day, scope.row.mealType)">
                    全部重换
                  </el-button>
                  <el-button 
                    size="small" 
                    plain
                    class="meal-manage-btn meal-btn-clear"
                    :disabled="scope.row.isPlaceholder" 
                    @click="deleteMeal(scope.row.day, scope.row.mealType)"
                  >
                    清空
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 推荐方案解释（加权评分：仅总评分） -->
        <div v-if="weightedExplanationOverall" class="plan-explain-section">
          <h4 class="plan-explain-title">为什么选择这个方案</h4>
          <div class="plan-explain-overall">
            方案总评分：
            <span class="plan-explain-strong">{{ weightedExplanationOverall.avgWeightedScore.toFixed(2) }}</span>/100
            ，优势：{{ weightedExplanationOverall.primaryAdvantageLabel }}
          </div>
        </div>
      </section>

      <!-- 空结果 -->
      <div class="empty-container" v-else>
        <el-empty
          description="暂无菜谱计划，请添加自己的配方或点击生成菜谱计划"
        >
          <el-button type="primary" @click="generateRecipePlan">生成菜谱计划</el-button>
        </el-empty>
      </div>

      <!-- 配方采购表 -->
      <section class="results-section" v-if="displayDishes.length > 0">
        <div class="section-header" @click="isProcurementExpanded = !isProcurementExpanded" style="cursor: pointer; display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <h3 style="margin: 0;">配方采购表</h3>
            <el-icon :style="{ transform: isProcurementExpanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.3s' }">
              <ArrowDown />
            </el-icon>
          </div>
          <div v-if="isProcurementExpanded" style="display:flex;gap:8px;align-items:center;">
            <template v-if="!isEditingProcurement">
              <el-button type="primary" @click.stop="startEditProcurement">修改</el-button>
              <el-button @click.stop="exportProcurementCSV">导出采购表</el-button>
            </template>
            <template v-else>
              <el-button @click.stop="addProcurementRow">新增行</el-button>
              <el-button type="primary" @click.stop="saveProcurement">保存</el-button>
              <el-button @click.stop="cancelEditProcurement">取消</el-button>
            </template>
          </div>
        </div>

        <el-collapse-transition>
          <div v-show="isProcurementExpanded">
            <div class="recipe-plan-table">
              <el-table
                :data="procurementTableData"
                stripe
                border
                style="width: 100%"
              >
                <el-table-column
                  prop="ingredient"
                  label="食材"
                  width="240"
                >
                  <template #default="scope">
                    <el-input v-if="isEditingProcurement" v-model="scope.row.ingredient" placeholder="请输入食材" />
                    <span v-else>{{ scope.row.ingredient }}</span>
                  </template>
                </el-table-column>
                <el-table-column
                  prop="total_grams"
                  label="总采购量(g)"
                  width="180"
                >
                  <template #default="scope">
                    <el-input-number
                      v-if="isEditingProcurement"
                      v-model="scope.row.total_grams"
                      :min="0"
                      :precision="1"
                      :step="1"
                      style="width: 140px;"
                    />
                    <span v-else>{{ Number(scope.row.total_grams || 0).toFixed(1) }}</span>
                  </template>
                </el-table-column>
                <el-table-column v-if="isEditingProcurement" label="操作" width="100">
                  <template #default="scope">
                    <el-button
                      size="small"
                      type="danger"
                      plain
                      class="procurement-btn-delete"
                      @click="removeProcurementRow(scope.$index)"
                    >
                      删除
                    </el-button>
                  </template>
                </el-table-column>
                <el-table-column
                  label="预计成本"
                  width="140"
                  align="right"
                >
                  <template #default="scope">
                    <template v-if="getProcurementRowEstimatedCost(scope.row).hasPrice">
                      <span class="cost-text procurement-cost-text">¥{{ getProcurementRowEstimatedCost(scope.row).cost.toFixed(2) }}</span>
                    </template>
                    <span v-else style="color: #c0c4cc; font-size: 12px;">未定价</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            <div v-if="procurementTableData.length > 0" class="procurement-summary" style="margin-top: 12px; padding: 12px; background: #fafafa; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
              <span style="color: #606266;">采购表预计总成本</span>
              <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 6px;">
                <span class="cost-text procurement-total-cost-text">¥{{ procurementTotalEstimatedCost.toFixed(2) }}</span>
                <span style="font-size: 12px; color: #909399;">
                  个人均成本（元/人）：¥{{ procurementPerCapitaEstimatedCost.toFixed(2) }}
                </span>
              </div>
            </div>
          </div>
        </el-collapse-transition>
      </section>

      <!-- 餐次修改弹窗 -->
      <el-dialog
        v-model="mealEditDialogVisible"
        :title="`修改 - 第${mealEditInfo.day}天 ${mealEditInfo.mealType}`"
        width="800px"
        destroy-on-close
        class="meal-edit-dialog"
      >
        <div class="meal-dishes-list">
          <el-table :data="mealEditInfo.dishes" border stripe>
            <el-table-column label="菜品名称" prop="name" min-width="150">
              <template #default="scope">
                <span style="font-weight: bold;">{{ scope.row.name }}</span>
                <div style="font-size: 12px; color: #909399;">{{ scope.row.category || dishTypeToText(scope.row.dish_type) }}</div>
              </template>
            </el-table-column>
            <el-table-column label="口味/份数" width="120" align="center">
              <template #default="scope">
                <el-tag size="small" type="info">{{ scope.row.flavor || '原味' }}</el-tag>
                <div style="margin-top: 4px;">{{ scope.row.servings }}份</div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="280" align="center">
              <template #default="scope">
                <div class="dialog-action-buttons">
                  <el-button size="small" plain class="meal-manage-btn meal-btn-edit" @click="editDishFromMealDialog(scope.row)">
                    修改详情
                  </el-button>
                  <el-button size="small" plain class="meal-manage-btn meal-btn-regen" @click="regenerateSingleDish(scope.row)">
                    重新生成
                  </el-button>
                  <el-button size="small" plain class="meal-manage-btn meal-btn-clear" @click="deleteDishFromMealDialog(scope.row)">
                    删除
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="mealEditDialogVisible = false" type="primary">完成</el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 修改菜品对话框 -->

      <el-dialog
        v-model="editDialogVisible"
        title="修改菜品"
        width="640px"
        destroy-on-close
      >
        <el-form
          v-if="currentDish"
          :model="currentDish"
          label-width="90px"
          label-position="left"
        >
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="天数">
                <el-input-number 
                  v-model="currentDish.day" 
                  :min="1" 
                  :max="7" 
                  :step="1" 
                  placeholder="请输入天数"
                ></el-input-number>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="餐饮类型">
                <el-select v-model="currentDish.time" placeholder="请选择餐饮类型">
                  <el-option label="早餐" value="早餐" />
                  <el-option label="午餐" value="午餐" />
                  <el-option label="晚餐" value="晚餐" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          
          <el-form-item label="菜品名称">
            <el-input v-model="currentDish.name" placeholder="请输入菜品名称" />
          </el-form-item>

          <el-form-item label="口味">
            <el-select v-model="currentDish.flavor" placeholder="请选择口味">
              <el-option label="原味" value="原味" />
              <el-option label="甜" value="甜" />
              <el-option label="咸" value="咸" />
              <el-option label="辣" value="辣" />
              <el-option label="酸" value="酸" />
              <el-option label="腥" value="腥" />
            </el-select>
          </el-form-item>

          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="份数">
                <el-input-number 
                  v-model="currentDish.servings" 
                  :min="1" 
                  :max="100" 
                  :step="1" 
                  placeholder="请输入份数"
                ></el-input-number>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="时令">
                <el-select v-model="currentDish.season" placeholder="请选择时令">
                  <el-option label="春季" value="春季" />
                  <el-option label="夏季" value="夏季" />
                  <el-option label="秋季" value="秋季" />
                  <el-option label="冬季" value="冬季" />
                  <el-option label="四季皆宜" value="四季皆宜" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="营养信息">
            <el-input
              v-model="currentDish.nutrition"
              type="textarea"
              :rows="5"
              placeholder="例如：卡路里：220 kcal，蛋白质：8 g，脂肪：10 g，碳水化合物：25 g"
            />
          </el-form-item>

          <el-form-item label="详细描述">
            <el-input
              v-model="currentDish.description"
              type="textarea"
              :rows="5"
              placeholder="请输入菜品描述"
            />
          </el-form-item>
        </el-form>

        <template #footer>
          <span class="dialog-footer">
            <el-button @click="editDialogVisible = false">取 消</el-button>
            <el-button type="primary" @click="saveEditedDish">保 存</el-button>
          </span>
        </template>
      </el-dialog>
      </main>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElLoading, type UploadFile } from 'element-plus'
import { Loading, ArrowDown, Plus, InfoFilled, Search, Opportunity, Upload, Document, View } from '@element-plus/icons-vue'
import { useRecommendationStore, useAuthStore, api as axios } from '../stores/auth'
import { dishTypeToText, dishTypeToBackend } from '../utils/constants'
import * as XLSX from 'xlsx'

const recStore = useRecommendationStore()
const authStore = useAuthStore()

const adminDiningStyle = ref('盘餐')
const adminMealPeople = ref<Record<'breakfast'|'lunch'|'dinner', number>>({
  breakfast: 1, lunch: 1, dinner: 1
})
const adminRulesLoaded = ref(false)
const hasSavedPlan = ref(false)

const fetchAdminRules = async () => {
  try {
    const rules = await recStore.api.get('/system/meal-rules')
    if (rules && rules.dining_style) adminDiningStyle.value = rules.dining_style
    if (rules && rules.num_people && typeof rules.num_people === 'object') {
      adminMealPeople.value = {
        breakfast: Number(rules.num_people.breakfast) || 1,
        lunch: Number(rules.num_people.lunch) || 1,
        dinner: Number(rules.num_people.dinner) || 1
      }
    }
    adminRulesLoaded.value = true
  } catch (err) {
    console.error('获取管理员规则失败:', err)
  }
}

onMounted(() => {
  fetchAdminRules()
})

const pad2 = (n: number) => String(n).padStart(2, '0')

const formatYMD = (d: Date) => {
  const year = d.getFullYear()
  const month = pad2(d.getMonth() + 1)
  const day = pad2(d.getDate())
  return `${year}-${month}-${day}`
}

const parseYMD = (s: string) => {
  const m = String(s || '').match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (!m) return null
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
  return isNaN(d.getTime()) ? null : d
}

const weekdayCN = (d: Date) => {
  const idx = d.getDay()
  return ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][idx] || ''
}

const formatApplyDate = (ymd: string) => {
  const d = parseYMD(ymd)
  if (!d) return String(ymd || '')
  const w = weekdayCN(d)
  return w ? `${ymd}（${w}）` : ymd
}

const addDaysYMD = (ymd: string, days: number) => {
  const base = parseYMD(ymd) || new Date()
  const d = new Date(base.getFullYear(), base.getMonth(), base.getDate())
  d.setDate(d.getDate() + Number(days || 0))
  return formatYMD(d)
}

const tomorrowDate = (() => {
  const t = new Date()
  t.setHours(0, 0, 0, 0)
  t.setDate(t.getDate() + 1)
  return t
})()

const tomorrowYMD = formatYMD(tomorrowDate)

const cleanDescription = (desc: string) => {
  if (!desc) return desc
  // 移除缩放说明：(已按学生餐营养指南：... 倍)
  const noteRegex = /\(已按学生餐营养指南：.*?倍\)/g
  return desc.replace(noteRegex, '').trim()
}

// 配方采购表是否展开
const isProcurementExpanded = ref(false)
const isEditingProcurement = ref(false)
const procurementSaved = ref<Array<{ ingredient: string; total_grams: number }> | null>(null)
const procurementDraft = ref<Array<{ ingredient: string; total_grams: number }>>([])

// 添加菜品搜索相关
const searchDishVisible = ref(false)
const searchLoading = ref(false)
const dbSearchResult = ref<any[]>([])
const selectedSearchDish = ref<any>(null)
const currentAddContext = ref<{ day: number; time: string } | null>(null)

// 加载进度相关
const loadingProgress = ref(0)
let loadingTimer: any = null

const startLoadingProgress = () => {
  loadingProgress.value = 0
  if (loadingTimer) clearInterval(loadingTimer)
  loadingTimer = setInterval(() => {
    if (loadingProgress.value < 90) {
      // 前期快，后期慢的模拟
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
  // 延迟一会再重置进度，让用户看到100%
  setTimeout(() => {
    if (!recStore.loading) {
      loadingProgress.value = 0
    }
  }, 500)
}

const dateMode = ref<'continuous' | 'custom'>('continuous')
const startDate = ref<string>(tomorrowYMD)

const customDateDialogVisible = ref(false)
const calendarValue = ref<Date>(new Date(tomorrowDate))
const customDates = ref<string[]>([])
const customDatesDraft = ref<string[]>([])

const baseCalendarYear = tomorrowDate.getFullYear()
const baseCalendarMonth = tomorrowDate.getMonth()

const customDatesSet = computed(() => new Set(customDatesDraft.value))

const disableStartDate = (d: Date) => {
  if (!d) return false
  const dt = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const min = new Date(tomorrowDate.getFullYear(), tomorrowDate.getMonth(), tomorrowDate.getDate())
  return dt.getTime() < min.getTime()
}

const isCustomDateDisabled = (d: Date) => {
  if (!d) return false
  const dt = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const min = new Date(tomorrowDate.getFullYear(), tomorrowDate.getMonth(), tomorrowDate.getDate())
  if (dt.getTime() < min.getTime()) return true
  return dt.getFullYear() !== baseCalendarYear || dt.getMonth() !== baseCalendarMonth
}

const normalizeAndSortDates = (dates: string[]) => {
  const list = Array.from(new Set((dates || []).filter(Boolean)))
  list.sort((a, b) => (a < b ? -1 : a > b ? 1 : 0))
  return list
}

const getPlanDates = () => {
  if (dateMode.value === 'custom') {
    return normalizeAndSortDates(customDates.value)
  }
  const days = Math.max(1, Math.min(7, Number(rulesForm.days || 1)))
  return Array.from({ length: days }, (_, i) => addDaysYMD(startDate.value || tomorrowYMD, i))
}

const getApplyDateForDay = (day: number) => {
  const idx = Math.max(0, Number(day || 1) - 1)
  const dates = getPlanDates()
  return dates[idx]
}

const openCustomDateDialog = () => {
  if (customDates.value.length === 0) {
    const days = Math.max(1, Math.min(7, Number(rulesForm.days || 1)))
    const seed = Array.from({ length: days }, (_, i) => addDaysYMD(tomorrowYMD, i))
    customDatesDraft.value = normalizeAndSortDates(seed)
  } else {
    customDatesDraft.value = normalizeAndSortDates(customDates.value)
  }
  calendarValue.value = new Date(tomorrowDate)
  customDateDialogVisible.value = true
}

const toggleCustomDate = (ymd: string, d: Date) => {
  if (isCustomDateDisabled(d)) return
  const set = new Set(customDatesDraft.value)
  if (set.has(ymd)) set.delete(ymd)
  else set.add(ymd)
  customDatesDraft.value = normalizeAndSortDates(Array.from(set))
}

const removeCustomDate = (ymd: string) => {
  customDatesDraft.value = customDatesDraft.value.filter(d => d !== ymd)
}

const cancelCustomDateDialog = () => {
  customDateDialogVisible.value = false
}

const confirmCustomDateDialog = () => {
  const list = normalizeAndSortDates(customDatesDraft.value)
  customDates.value = list
  rulesForm.days = Math.max(1, Math.min(7, list.length || 1))
  customDateDialogVisible.value = false
}

// 搜索数据库中的菜品
const searchDishesFromDB = async (query: string) => {
  if (query) {
    searchLoading.value = true
    try {
      // 使用 recStore.api (axios 实例) 直接请求 menu_items 接口
      const data = await recStore.api.get('/menu_items/', {
        params: { keyword: query, limit: 20 }
      })
      dbSearchResult.value = data || []
    } catch (error) {
      console.error('搜索菜品失败:', error)
    } finally {
      searchLoading.value = false
    }
  } else {
    dbSearchResult.value = []
  }
}

// 打开搜索弹窗
const openAddDishSearch = (day: number, time: string) => {
  currentAddContext.value = { day, time }
  searchDishVisible.value = true
  selectedSearchDish.value = null
  dbSearchResult.value = []
}

// 确认添加菜品到餐次
const confirmAddDishToMeal = () => {
  if (!currentAddContext.value || !selectedSearchDish.value) return

  const item = selectedSearchDish.value
  const newDish = {
    id: item.id,
    name: item.dish_name,
    dish_type: item.dish_type,
    category: item.category || '',
    flavor: item.flavor,
    season: item.season,
    servings: rulesForm.servings || 1,
    description: item.dish_recipe || '',
    ingredients: item.dish_recipe || '', // 暂时用配方填充食材
    nutrition: `卡路里:${item.total_calories} 蛋白质:${item.total_protein} 碳水:${item.total_carbohydrates} 脂肪:${item.total_fat}`,
    apply_date: getApplyDateForDay(currentAddContext.value.day),
    day: currentAddContext.value.day,
    time: currentAddContext.value.time
  }

  recipePlan.value.push(newDish)
  
  // 清除对应的营养总结（因为餐次内容已变）
  const mealKey = dishTypeToBackend(newDish.time)
  const summaryKey = `${newDish.day}_${mealKey}`
  if (mealSummaries.value[summaryKey]) {
    delete mealSummaries.value[summaryKey]
  }

  ElMessage.success(`已添加 ${newDish.name}`)
  searchDishVisible.value = false
}

// 模式切换：true=AI, false=Database
const isAiMode = ref(true)

/** 合并服务端有效价格（每克）：与 loadSavedPlan 后的本地映射合并，同名键以数据库为准（不写入「已有食材」标签，避免整库刷屏） */
async function mergeEffectivePricesFromServer() {
  try {
    const result = await axios.get('/ingredient_prices/effective-price-map')
    if (result && result.prices && typeof result.prices === 'object') {
      const prices = result.prices as Record<string, number>
      ingredientPrices.value = { ...ingredientPrices.value, ...prices }
    }
  } catch (err) {
    console.error('加载有效食材价格失败:', err)
  }
}

// 页面挂载时，从localStorage恢复未完成的菜谱计划，并合并数据库中的有效食材价格（供应商价+参考价），供采购表预计成本使用
onMounted(async () => {
  loadSavedPlan()
  await mergeEffectivePricesFromServer()
})

// 已有食材输入与标签
const ingredientInput = ref<string>('')
const availableIngredients = ref<string[]>([])
const ingredientPrices = ref<Record<string, number>>({})
/** 价格映射条目数（用于导入成功提示，不占用「已有食材」标签区） */
const ingredientPriceEntryCount = computed(() => Object.keys(ingredientPrices.value).length)
const importedFileName = ref<string>('')

const clearImportedFile = async () => {
  importedFileName.value = ''
  await mergeEffectivePricesFromServer()
  ElMessage.info('已清除导入文件标记，仍从数据库加载参考价格')
}

// 上传组件引用
const previewUploadRef = ref<any>(null)
const importUploadRef = ref<any>(null)
const previewData = ref<any>(null)
const previewDialogVisible = ref(false)

// 触发预览上传
const triggerPreviewUpload = () => {
  previewUploadRef.value?.$el?.querySelector('input')?.click()
}

// 触发导入上传
const triggerImportUpload = () => {
  importUploadRef.value?.$el?.querySelector('input')?.click()
}

// 预览成本表格
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

    const result = await axios.post('/supplier-price-import/preview-supplier-prices', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    loading.close()

    // axios 响应拦截器已返回 response.data，result 即接口返回体
    if (result) {
      previewData.value = result
      previewDialogVisible.value = true

      // 检查必要列是否缺失
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
    console.error('Preview error:', err)
    const errorMsg = err.response?.data?.detail || '预览失败，请检查文件格式'
    ElMessage.error(errorMsg)
  }

  // 清空上传组件，允许重复选择同一文件
  previewUploadRef.value?.clearFiles?.()
}

const addIngredient = () => {
  const v = (ingredientInput.value || '').trim()
  if (!v) return
  if (!availableIngredients.value.includes(v)) {
    availableIngredients.value.push(v)
  }
  ingredientInput.value = ''
}
const removeIngredient = (index: number) => {
  if (index >= 0 && index < availableIngredients.value.length) {
    availableIngredients.value.splice(index, 1)
  }
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
    // 创建 FormData 用于上传文件
    const formData = new FormData()
    formData.append('file', file.raw)

    // 调用后端 API 导入供应商价格表
    const result = await axios.post('/supplier-price-import/import-supplier-prices', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    loading.close()

    // axios 响应拦截器已返回 response.data，result 即接口返回体
    if (result && result.success) {
      const stats = result.stats
      ElMessage.success(
        `导入成功！共处理 ${stats.total} 条，成功导入 ${stats.success} 条，` +
        `新建一级分类 ${stats.l1_created} 个，二级分类 ${stats.l2_created} 个`
      )

      // 保存文件名和导入状态
      importedFileName.value = file.name

      // 刷新食材列表（从导入的分类中提取食材名称）
      await refreshImportedIngredients()

      // 如果导入成功，同时更新推荐页面的食材价格映射
      if (result.columns_detected && result.columns_detected.price) {
        ElMessage.info('已自动提取价格信息，可在推荐时使用')
      }
    } else {
      ElMessage.warning(result?.message || '导入完成，但可能有部分数据未处理')
    }

    // 如果存在错误，显示详细信息
    if (result?.stats?.errors && result.stats.errors.length > 0) {
      const errorCount = result.stats.errors.length
      if (errorCount <= 3) {
        result.stats.errors.forEach((err: string) => {
          ElMessage.error(err)
        })
      } else {
        ElMessage.error(`有 ${errorCount} 条数据导入失败，请检查数据格式`)
        console.error('导入错误详情:', result.stats.errors)
      }
    }
  } catch (err: any) {
    loading.close()
    console.error('Import error:', err)
    console.error('Error response:', err.response)
    console.error('Error response data:', err.response?.data)

    // 构建详细的错误信息
    let errorMsg = '导入失败'
    if (err.response?.data?.detail) {
      errorMsg = err.response.data.detail
    } else if (err.message) {
      errorMsg = `导入失败: ${err.message}`
    }

    ElMessage.error(errorMsg)

    // 如果是列名检测错误，显示更详细的提示
    if (err.response?.data?.detail?.includes('未找到') || err.response?.status === 400) {
      ElMessage.info('支持的列名：一级分类/大分类/分类/品类、食材名称/品名/名称/商品、价格/单价/金额/元、单位、二级分类/小分类等')
      ElMessage.info('请确保Excel表格的列名与上述名称匹配')
    }

    // 如果是404错误，说明API不存在，需要重启后端
    if (err.response?.status === 404) {
      ElMessage.error('API接口不存在，请重启后端服务后重试')
      console.error('API 404: /supplier-price-import/import-supplier-prices 未找到')
    }
  }
}

// 刷新有效价格映射（导入供应商表后全量以服务端为准；不覆盖「已有食材」列表）
const refreshImportedIngredients = async () => {
  try {
    const result = await axios.get('/ingredient_prices/effective-price-map')
    if (result && result.prices && typeof result.prices === 'object') {
      const prices = result.prices as Record<string, number>
      ingredientPrices.value = { ...prices }
    }
  } catch (err) {
    console.error('刷新有效价格失败:', err)
  }
}

// 修改对话框相关
const editDialogVisible = ref(false)
const currentDish = ref<any>(null)
const editIndex = ref<number>(-1)

// 餐次修改弹窗相关
const mealEditDialogVisible = ref(false)
const mealEditInfo = ref<{day: number, mealType: string, dishes: any[]}>({
  day: 0,
  mealType: '',
  dishes: []
})

const openMealEdit = (day: number, mealType: string) => {
  const dishes = recipePlan.value.filter(d => Number(d.day) === Number(day) && String(d.time) === mealType)
  mealEditInfo.value = {
    day,
    mealType,
    dishes: dishes // 这里直接引用，方便同步修改
  }
  mealEditDialogVisible.value = true
}

const deleteDishFromMealDialog = (dish: any) => {
  deleteMealDish(dish)
  // 同步更新弹窗内的列表
  mealEditInfo.value.dishes = mealEditInfo.value.dishes.filter(d => d.id !== dish.id)
  if (mealEditInfo.value.dishes.length === 0) {
    mealEditDialogVisible.value = false
  }
}

const editDishFromMealDialog = (dish: any) => {
  handleEditDish(dish)
}

const regenerateSingleDish = async (dish: any) => {
  try {
    const loading = ElLoading.service({ text: '正在重新生成菜品...', background: 'rgba(255, 255, 255, 0.7)' })
    
    // 重新生成的规则：餐品的类型（餐次）与种类（分类）必须与原菜品一致
    // 转换餐次为后端识别的英文
    let baseType = dishTypeToBackend(dish.time || mealEditInfo.value.mealType)
    const baseCategory = dish.category
    
    console.log('重新生成单菜请求:', {
      originalDish: dish,
      baseType,
      baseCategory,
      excludeId: dish.id
    })

    // 1. 严格匹配：餐次 + 分类 + 排除当前 ID
    const params = {
      dish_type: [baseType],
      category: baseCategory ? [baseCategory] : [],
      exclude_ids: [dish.id],
      count: 1,
      ingredients: availableIngredients.value,
      ingredient_prices: ingredientPrices.value,
    }

    let data = await axios.post('/recommendation/database-recommendation', params)
    console.log('第一轮(严格)结果:', data)
    
    // 2. 如果严格匹配（餐次+分类）没找到，尝试放宽餐次限制，仅匹配分类
    if (!(data && data.length > 0)) {
      console.log('严格匹配未找到，尝试仅根据分类搜索...')
      const relaxedParams = {
        category: baseCategory ? [baseCategory] : [],
      exclude_ids: [dish.id],
      count: 1,
      ingredients: availableIngredients.value,
      ingredient_prices: ingredientPrices.value,
    }
      data = await axios.post('/recommendation/database-recommendation', relaxedParams)
      console.log('第二轮(分类)结果:', data)
    }

    // 3. 如果还是没找到，尝试仅根据餐次搜索
    if (!(data && data.length > 0)) {
      console.log('分类匹配也未找到，尝试仅根据餐次搜索...')
      const fallbackParams = {
        dish_type: [baseType],
      exclude_ids: [dish.id],
      count: 1,
      ingredients: availableIngredients.value,
      ingredient_prices: ingredientPrices.value,
    }
      data = await axios.post('/recommendation/database-recommendation', fallbackParams)
      console.log('第三轮(餐次)结果:', data)
    }

    loading.close()

    if (data && data.length > 0) {
      const newDishData = data[0]
      // 查找在主计划中的索引
      // 这里的匹配需要更健壮，支持中文和英文的 time/mealType 匹配
      const index = recipePlan.value.findIndex(d => {
        const isSameId = d.id === dish.id
        const isSameDay = Number(d.day) === Number(dish.day)
        
        // 转换两边的时间为英文进行比较
        const dTimeEng = dishTypeToBackend(d.time)
        const dishTimeEng = dishTypeToBackend(dish.time)
        const isSameTime = dTimeEng === dishTimeEng
        
        return isSameId && isSameDay && isSameTime
      })
      
      console.log('在 recipePlan 中查找结果:', { index, found: index !== -1 })
      
      if (index !== -1) {
        const nutritionText = [
          `卡路里: ${newDishData.total_calories}kcal`,
          `蛋白质: ${newDishData.total_protein}g`,
          `脂肪: ${newDishData.total_fat}g`,
          `碳水: ${newDishData.total_carbohydrates}g`
        ].join(' | ')

        const updatedDish = {
          ...recipePlan.value[index],
          id: newDishData.id,
          name: newDishData.dish_name,
          dish_type: newDishData.dish_type,
          category: newDishData.category || '',
          flavor: newDishData.flavor,
          season: newDishData.season,
          description: newDishData.dish_recipe,
          ingredients: newDishData.dish_recipe,
          nutrition: nutritionText,
          original_data: newDishData
        }

        recipePlan.value[index] = updatedDish
        
        // 团餐模式下，单菜更换后营养总结失效，需要清除
        const mealKey = dishTypeToBackend(dish.time)
        const summaryKey = `${dish.day}_${mealKey}`
        if (mealSummaries.value[summaryKey]) {
          delete mealSummaries.value[summaryKey]
        }
        
        // 同步更新弹窗内的列表数据
        const dialogDishIndex = mealEditInfo.value.dishes.findIndex(d => d.id === dish.id)
        if (dialogDishIndex !== -1) {
          mealEditInfo.value.dishes[dialogDishIndex] = updatedDish
        }

        ElMessage.success('菜品已重新生成')
      } else {
        console.warn('未能在 recipePlan 中找到原菜品，可能已被修改或删除')
        ElMessage.warning('未能同步更新计划，请刷新后重试')
      }
    } else {
      ElMessage.warning('未能找到合适的替代菜品')
    }
  } catch (error) {
    console.error('重新生成菜品失败:', error)
    ElMessage.error('重新生成菜品失败')
  }
}

// AI 营养分析相关
const analyzePlanWithAI = async (planMeals: any[], planId: string | number) => {
  if (!planMeals || planMeals.length === 0) return
  
  try {
    // 1. 构造菜谱文本描述
    const planText = planMeals.map(m => {
      return `第${m.day}天 ${m.time}: ${m.name} (${m.nutrition || '无营养数据'})`
    }).join('\n')

    const query = `根据我的菜谱计划：\n${planText}\n进行分析：\n1. 营养总结：核心亮点与主要不足。\n2. 计划推荐：未来最优先的一项调整建议。`

    // 2. 调用 Dify API
    const response = await fetch('http://localhost/v1/chat-messages', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer app-XAjrMlkWgnjFLTmChjfa8ZT2', // 更新为正确密钥
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        inputs: {},
        query: query,
        response_mode: 'blocking',
        user: authStore.user?.username || 'guest_user'
      })
    })

    if (!response.ok) {
      throw new Error('AI 分析请求失败')
    }

    const data = await response.json()
    const answer = data.answer || '未能获取到分析结果'
    
    // 3. 将结果存储在 localStorage 中，键名为 plan_analysis_{userId}_{planId}
    // 首页将根据当前展示的最新 planId 来读取对应的分析
    const userId = authStore.user?.id || 'default'
    localStorage.setItem(`plan_analysis_${userId}_${planId}`, answer)
    console.log('AI 分析已完成并存入本地存储')
  } catch (error) {
    console.error('AI 静默分析出错:', error)
  }
}

// 自定义添加的菜品
const customDishes = ref<any[]>([])
// 生成的菜谱计划
const recipePlan = ref<any[]>([])
// 团餐模式下的营养总结
const mealSummaries = ref<Record<string, any>>({})
// 用于保存的临时计划
const tempPlan = ref<any[]>([])

// 获取当前季节
function getCurrentSeason() {
  const month = new Date().getMonth() + 1
  if (month >= 3 && month <= 5) return '春季'
  if (month >= 6 && month <= 8) return '夏季'
  if (month >= 9 && month <= 11) return '秋季'
  return '冬季'
}

// 推荐规则表单
const rulesForm = reactive({
  dishType: [] as string[],
  flavor: [] as string[],
  season: [getCurrentSeason()] as string[],
  days: 1,
  servings: 1,
  num_people: 1,
  target_age_group: undefined as string | undefined,
  mealSettings: {
    '早餐': { num_people: undefined as number | undefined, age_group: undefined as string | undefined },
    '午餐': { num_people: undefined as number | undefined, age_group: undefined as string | undefined },
    '晚餐': { num_people: undefined as number | undefined, age_group: undefined as string | undefined },
  } as Record<string, { num_people?: number, age_group?: string }>,
  nutritionRequirements: [] as string[],
})

watch(
  () => [...rulesForm.season],
  (newVal) => {
    if (!Array.isArray(newVal) || newVal.length === 0) {
      rulesForm.season = ['四季皆宜']
      return
    }
    if (newVal.includes('四季皆宜') && newVal.length > 1) {
      rulesForm.season = newVal.filter(s => s !== '四季皆宜')
    }
  },
  { deep: false }
)

// 计算属性：当前显示的菜品列表
const displayDishes = computed(() => {
  return [...customDishes.value, ...recipePlan.value]
})

const groupedRows = computed(() => {
  const map: Record<number, any> = {}
  for (const item of recipePlan.value) {
    const day = Number(item.day) || 1
    if (!map[day]) {
      map[day] = { day, apply_date: item.apply_date || null, breakfast: [], lunch: [], dinner: [] }
    } else if (!map[day].apply_date && item.apply_date) {
      map[day].apply_date = item.apply_date
    }
    const t = String(item.time)
    if (t === '早餐') map[day].breakfast.push(item)
    else if (t === '午餐') map[day].lunch.push(item)
    else if (t === '晚餐') map[day].dinner.push(item)
  }
  return Object.values(map).sort((a, b) => a.day - b.day)
})

// 计算单餐次能量总和
const calculateMealEnergy = (dishes: any[]) => {
  if (!dishes || dishes.length === 0) return 0
  let total = 0
  dishes.forEach(dish => {
    const nutrition = dish.nutrition || ''
    // 尝试匹配卡路里或能量数值
    // 格式通常为 "卡路里:220 蛋白质:8 ..." 或 "卡路里：220 kcal ..."
    const match = nutrition.match(/(?:卡路里|能量)[:：]\s*(\d+(?:\.\d+)?)/)
    if (match && match[1]) {
      total += parseFloat(match[1]) * (Number(dish.servings) || 1)
    }
  })
  return total.toFixed(1)
}

const parseIngredientsFromText = (text: string) => {
  const out: Array<{ name: string; grams: number }> = []
  if (!text) return out
  
  // 1. 首先清理掉所有括号及其内部内容，因为它们通常是描述信息（如：辣椒(红，尖，干)）
  // 支持中英文括号
  const cleanedText = text.replace(/\(.*?\)|\（.*?\）/g, ' ')
  
  // 2. 使用更加鲁棒的正则：支持单行多个、多种分隔符、多种单位
  // 匹配模式：食材名 + 数字 + 单位
  // [^\s\d,，、:：]+ 表示匹配非空白、非数字、非分隔符的字符作为食材名
  const regex = /([^\s\d,，、:：]+)\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)\s*(g|克|mg|毫克|kg|千克|公斤|斤|两)\b/gi
  
  let match
  while ((match = regex.exec(cleanedText)) !== null) {
    let name = match[1].trim()
    const val = parseFloat(match[2])
    const unit = match[3].toLowerCase()
    
    let grams = 0
    if (unit === 'g' || unit === '克') {
      grams = val
    } else if (unit === 'mg' || unit === '毫克') {
      grams = val / 1000
    } else if (unit === 'kg' || unit === '千克' || unit === '公斤') {
      grams = val * 1000
    } else if (unit === '斤') {
      grams = val * 500
    } else if (unit === '两') {
      grams = val * 50
    }
    
    if (name && grams > 0) {
      // 进一步清理名称中的无关字符（如列表符号）
      name = name.replace(/^[-+*]\s*/, '').trim()
      // 如果清理后还有内容，则加入结果
      if (name) {
        out.push({ name, grams })
      }
    }
  }
  return out
}

const baseProcurementRows = computed(() => {
  const acc = new Map<string, { ingredient: string; total_grams: number }>()
  const all = [...displayDishes.value]
  for (const d of all) {
    // 优先尝试从 ingredients 字段提取，如果没有则从 description (dish_recipe) 提取
    const sourceText = (d.ingredients || d.description || d.dish_recipe || '')
    const items = parseIngredientsFromText(sourceText)
    const servings = Number(d.servings) || 1
    for (const it of items) {
      const key = it.name.toLowerCase().replace(/\s+/g, '')
      const add = it.grams * servings
      if (acc.has(key)) {
        const cur = acc.get(key)!
        cur.total_grams += add
      } else {
        acc.set(key, { ingredient: it.name, total_grams: add })
      }
    }
  }
  return Array.from(acc.values()).sort((a, b) => a.ingredient.localeCompare(b.ingredient, 'zh-CN'))
})

const procurementRows = computed(() => {
  const saved = procurementSaved.value
  if (Array.isArray(saved) && saved.length > 0) return saved
  return baseProcurementRows.value
})

const procurementTableData = computed(() => (isEditingProcurement.value ? procurementDraft.value : procurementRows.value))

// 根据食材名称在价格表中找最佳匹配的每克价
// - 配方名包含价格键（如「鸡蛋」含「鸡」「鸡蛋」）：取最长键，避免「鸡蛋」误用「鸡」的单价
// - 价格键包含配方名（如短名「鸡」）：取最短键，避免「鸡」误匹配超长 SKU 名导致天价
function getPricePerGramForIngredient(ingredientName: string): number | null {
  const prices = ingredientPrices.value
  if (!prices || !ingredientName) return null
  const r = String(ingredientName).trim()
  if (!r) return null
  if (prices[r] != null) return Number(prices[r])

  const keys = Object.keys(prices).filter(k => String(k).trim().length > 0)

  const recipeContainsKey = keys.filter(k => r.includes(k))
  if (recipeContainsKey.length > 0) {
    const best = recipeContainsKey.reduce((a, b) => (a.length >= b.length ? a : b))
    return Number(prices[best])
  }

  const keyContainsRecipe = keys.filter(k => k.includes(r))
  if (keyContainsRecipe.length > 0) {
    const best = keyContainsRecipe.reduce((a, b) => (a.length <= b.length ? a : b))
    return Number(prices[best])
  }

  return null
}

// 单行预计成本：总克数 × 每克价
function getProcurementRowEstimatedCost(row: { ingredient: string; total_grams?: number }): { cost: number; hasPrice: boolean } {
  const grams = Number(row?.total_grams) || 0
  const perGram = getPricePerGramForIngredient(String(row?.ingredient || '').trim())
  if (perGram == null) return { cost: 0, hasPrice: false }
  return { cost: grams * perGram, hasPrice: true }
}

// 配方采购表预计总成本（当前表格中所有行的预计成本之和，编辑时按草稿算）
const procurementTotalEstimatedCost = computed(() => {
  const rows = procurementTableData.value || []
  return rows.reduce((sum, row) => sum + getProcurementRowEstimatedCost(row).cost, 0)
})

// 人均成本（元/人）：总成本 ÷（天数 * 每日人数）
// - 团餐模式：每日人数取早/中/晚配置的平均值
// - 盘餐模式：每日人数取页面 servings
const procurementPeoplePerDay = computed(() => {
  if (adminDiningStyle.value === '团餐') {
    const mealKeys = (rulesForm.dishType || []).map((cn: string) => dishTypeToBackend(cn))
    const vals = mealKeys
      .map((k: any) => Number(adminMealPeople.value[k] || 1))
      .filter((v: number) => v >= 1)
    if (vals.length === 0) return 1
    return vals.reduce((a: number, b: number) => a + b, 0) / vals.length
  }

  return Math.max(1, Number(rulesForm.servings || 1))
})

const procurementPerCapitaEstimatedCost = computed(() => {
  const daysCount = Math.max(1, Number(rulesForm.days || 1))
  const people = Math.max(1, Number(procurementPeoplePerDay.value || 1))
  const denom = daysCount * people
  if (denom <= 0) return 0
  return procurementTotalEstimatedCost.value / denom
})

// 计算整份计划的总成本
const totalPlanCost = computed(() => {
  return displayDishes.value.reduce((sum, dish) => {
    const price = Number(dish.cost_price) || 0
    const servings = Number(dish.servings) || 1
    return sum + (price * servings)
  }, 0).toFixed(2)
})

const startEditProcurement = () => {
  procurementDraft.value = (procurementRows.value || []).map((r: any) => ({
    ingredient: String(r?.ingredient || ''),
    total_grams: Number(r?.total_grams) || 0
  }))
  isEditingProcurement.value = true
}

const cancelEditProcurement = () => {
  isEditingProcurement.value = false
  procurementDraft.value = []
}

const addProcurementRow = () => {
  procurementDraft.value.push({ ingredient: '', total_grams: 0 })
}

const removeProcurementRow = (idx: number) => {
  if (idx < 0 || idx >= procurementDraft.value.length) return
  procurementDraft.value.splice(idx, 1)
}

const persistPlanToStorage = () => {
  if (!authStore.user?.id) return
  const planData = {
    customDishes: customDishes.value,
    recipePlan: recipePlan.value,
    mealSummaries: mealSummaries.value,
    rulesForm: rulesForm,
    availableIngredients: availableIngredients.value,
    ingredientPrices: ingredientPrices.value,
    procurementSaved: procurementSaved.value,
    savedAt: new Date().toISOString()
  }
  localStorage.setItem(`recipePlan_user_${authStore.user.id}`, JSON.stringify(planData))
}

const saveProcurement = () => {
  const rows = (procurementDraft.value || [])
    .map(r => ({ ingredient: String(r.ingredient || '').trim(), total_grams: Number(r.total_grams) || 0 }))
    .filter(r => r.ingredient)
  procurementSaved.value = rows
  persistPlanToStorage()
  isEditingProcurement.value = false
  procurementDraft.value = []
  ElMessage.success('配方采购表已保存')
}

const exportProcurementCSV = () => {
  const rows = procurementRows.value
  if (!rows || rows.length === 0) {
    ElMessage.warning('当前采购表为空')
    return
  }
  const header = ['食材', '总采购量(g)', '预计成本(元)']
  const lines = [header.join(',')]
  for (const r of rows) {
    const ing = String(r.ingredient).replace(/"/g, '""')
    const val = (Number(r.total_grams) || 0).toFixed(1)
    const cost = getProcurementRowEstimatedCost(r)
    const costStr = cost.hasPrice ? cost.cost.toFixed(2) : ''
    lines.push(`"${ing}",${val},${costStr}`)
  }
  const csvContent = '\ufeff' + lines.join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  a.href = url
  a.download = `配方采购表_${y}${m}${d}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  ElMessage.success('已导出采购表')
}

// 获取数据库推荐 (迁移自 DatabaseRecommendationView.vue)
const getDatabaseRecommendation = async () => {
  try {
    recStore.loading = true
    recStore.error = null
    
    // 处理季节参数：确保包含"四季皆宜"
    let seasonParams = [...(rulesForm.season || [])]
    if (!seasonParams.includes('四季皆宜')) {
      seasonParams.push('四季皆宜')
    }
    
    const params = {
      dish_type: rulesForm.dishType.map(dishTypeToBackend),
      flavor: rulesForm.flavor,
      season: seasonParams,
      count: Math.min(20, rulesForm.days * rulesForm.dishType.length),
      nutrition_requirements: rulesForm.nutritionRequirements,
      ingredients: availableIngredients.value
    }
    
    await recStore.getDatabaseRecommendation(params)
    return recStore.databaseRecommendations
  } catch (error: any) {
    console.error('获取推荐失败:', error)
    let errorMessage = '获取推荐失败，请稍后重试'
    if (error.response?.data?.detail) {
        errorMessage = typeof error.response.data.detail === 'object' 
            ? (error.response.data.detail.message || JSON.stringify(error.response.data.detail)) 
            : error.response.data.detail
    } else if (error.message) {
      errorMessage = error.message
    }
    recStore.error = errorMessage
    ElMessage.error(`操作失败：${errorMessage}`)
    return []
  } finally {
    recStore.loading = false
  }
}

const regenerateMeal = async (day: number, mealType: string) => {
  try {
    if (!adminRulesLoaded.value) {
      await fetchAdminRules()
    }
    recStore.loading = true
    recStore.error = null
    startLoadingProgress()
    const backendType = dishTypeToBackend(mealType)
    
    // 处理季节参数：确保包含"四季皆宜"
    let seasonParams = [...(rulesForm.season || [])]
    if (!seasonParams.includes('四季皆宜')) {
      seasonParams.push('四季皆宜')
    }
    
    // 准备该餐次的特定设置
    const mealSettingsMap: Record<string, any> = {}
    const setting = rulesForm.mealSettings[mealType]
    if (setting && (setting.num_people || setting.age_group)) {
      mealSettingsMap[backendType] = {
        num_people: setting.num_people,
        target_age_group: setting.age_group
      }
    }

    const data = await recStore.api.post('/recommendation/meal-set-recommendation', {
      days: 1,
      meal_types: [backendType],
      flavor: rulesForm.flavor,
      season: seasonParams,
      nutrition_requirements: rulesForm.nutritionRequirements,
      ingredients: availableIngredients.value,
      ingredient_prices: ingredientPrices.value,
      target_age_group: rulesForm.target_age_group,
      servings: rulesForm.servings
    })

    const dayObj = (data?.days && Array.isArray(data.days) && data.days[0]) ? data.days[0] : null
    const list = (dayObj && Array.isArray(dayObj[backendType])) ? dayObj[backendType] : []

    // 更新营养总结
    const summaryKey = `${day}_${backendType}`
    if (dayObj && dayObj[`${backendType}_summary`]) {
      mealSummaries.value[summaryKey] = dayObj[`${backendType}_summary`]
    }

    // 确定该餐次的实际份数：团餐使用管理员配置的人数；盘餐使用页面份数
    let actualServings = rulesForm.servings
    if (adminDiningStyle.value === '团餐') {
      // 默认用管理员配置人数（早/中/晚），与后端团餐计算保持一致
      actualServings = adminMealPeople.value[backendType] || 1
    }

    recipePlan.value = recipePlan.value.filter(d => !(Number(d.day) === Number(day) && String(d.time) === mealType))

    const applyDate = getApplyDateForDay(day)
    for (const dish of list) {
      const nutritionText = [
        `能量：${dish.total_calories || 0} kcal`,
        `蛋白质：${dish.total_protein || 0} g`,
        `脂肪：${dish.total_fat || 0} g`,
        `碳水：${dish.total_carbohydrates || 0} g`
      ].join(' | ')
      recipePlan.value.push({
        id: dish.id,
        day: day,
        time: mealType,
        apply_date: applyDate,
        name: dish.dish_name,
        dish_type: dish.dish_type,
        category: dish.category || '',
        flavor: dish.flavor,
        season: dish.season,
        description: dish.dish_recipe,
        ingredients: dish.dish_recipe,
        nutrition: nutritionText,
        servings: actualServings,
        cost_price: dish.cost_price || 0,
        original_data: dish,
        is_custom: false
      })
    }
    if (list.length === 0) {
      ElMessage.warning('没有找到符合规则的推荐菜品')
    } else {
      ElMessage.success(`已全部重换第${day}天${mealType}`)
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '全部重换失败')
  } finally {
    recStore.loading = false
    stopLoadingProgress()
  }
}

// 替换单个菜品

// 生成菜谱计划
const generateRecipePlan = async () => {
  if (rulesForm.dishType.length === 0) {
    ElMessage.warning('请至少选择一种餐饮类型')
    return
  }
  
  if (!adminRulesLoaded.value) {
    await fetchAdminRules()
  }
  
  if (dateMode.value === 'custom' && customDates.value.length === 0) {
    openCustomDateDialog()
    ElMessage.warning('请选择要应用的日期')
    return
  }

  try {
    recStore.loading = true
    startLoadingProgress()
    const planDates = getPlanDates()
    const totalDays = Math.max(1, Math.min(7, planDates.length || Number(rulesForm.days || 1)))
    rulesForm.days = totalDays

    // 处理季节参数：确保包含"四季皆宜"，这样"四季皆宜"的菜品在任何季节都能被匹配到
    let seasonParams = [...(rulesForm.season || [])]
    if (!seasonParams.includes('四季皆宜')) {
      seasonParams.push('四季皆宜')
    }

    const mealTypesBackend = rulesForm.dishType.map(dishTypeToBackend)

    const data = await recStore.api.post('/recommendation/meal-set-recommendation', {
      days: totalDays,
      meal_types: mealTypesBackend,
      flavor: rulesForm.flavor,
      season: seasonParams,
      nutrition_requirements: rulesForm.nutritionRequirements,
      ingredients: availableIngredients.value,
      ingredient_prices: ingredientPrices.value,
      target_age_group: rulesForm.target_age_group,
      servings: rulesForm.servings
    })

    recipePlan.value = []
    mealSummaries.value = {}
    const daysArr = Array.isArray(data?.days) ? data.days : []
    for (const dayObj of daysArr) {
      const day = Number(dayObj?.day) || 1
      const applyDate = planDates[day - 1] || getApplyDateForDay(day)
      for (const mealTypeCn of rulesForm.dishType) {
        const mealKey = dishTypeToBackend(mealTypeCn)
        
        // 保存营养总结
        const summaryKey = `${day}_${mealKey}`
        if (dayObj[`${mealKey}_summary`]) {
          mealSummaries.value[summaryKey] = dayObj[`${mealKey}_summary`]
        }

        // 确定该餐次的实际份数（用于展示/采购表计算）
        // 默认在团餐模式下：优先用管理员配置的早/中/晚人数；避免仍然显示“一份(1)”。
        let actualServings = rulesForm.servings
        if (adminDiningStyle.value === '团餐') {
          const mealSetting = rulesForm.mealSettings[mealTypeCn]
          if (mealSetting && mealSetting.num_people) {
            actualServings = mealSetting.num_people
          } else if (Number(actualServings) <= 1) {
            const cfgPeople = adminMealPeople.value[mealKey as 'breakfast'|'lunch'|'dinner'] || 1
            if (cfgPeople > 1) actualServings = cfgPeople
            else if (rulesForm.num_people && rulesForm.num_people > 1) actualServings = rulesForm.num_people
          }
        }

        const list = Array.isArray(dayObj?.[mealKey]) ? dayObj[mealKey] : []
        for (const dish of list) {
          const nutritionText = [
            `能量：${dish.total_calories || 0} kcal`,
            `蛋白质：${dish.total_protein || 0} g`,
            `脂肪：${dish.total_fat || 0} g`,
            `碳水：${dish.total_carbohydrates || 0} g`
          ].join(' | ')
          recipePlan.value.push({
            id: dish.id,
            day: day,
            time: mealTypeCn,
            apply_date: applyDate,
            name: dish.dish_name,
            dish_type: dish.dish_type,
            category: dish.category || '',
            flavor: dish.flavor,
            season: dish.season,
            description: dish.dish_recipe,
            ingredients: dish.dish_recipe,
            nutrition: nutritionText,
            servings: actualServings,
            cost_price: dish.cost_price || 0,
            original_data: dish,
            is_custom: false
          })
        }
      }
    }

    if (recipePlan.value.length === 0) {
      ElMessage.warning('没有生成任何菜品，请检查管理员配餐规则与菜品类别数据')
    } else {
      ElMessage.success(`成功生成 ${recipePlan.value.length} 道菜品的菜谱计划`)
    }
  } catch (error: any) {
    console.error('生成菜谱计划失败:', error)
    ElMessage.error('生成菜谱计划失败')
  } finally {
    recStore.loading = false
    stopLoadingProgress()
  }
}

// 重置规则
const resetRules = () => {
  Object.assign(rulesForm, {
    dishType: [],
    flavor: [],
    season: [getCurrentSeason()],
    days: 1,
    servings: 1,
    num_people: 1,
    nutritionRequirements: []
  })
  recipePlan.value = []
  mealSummaries.value = {}
}

// 保存菜谱计划到localStorage
const savePlan = () => {
  if (!authStore.user?.id) {
    ElMessage.warning('登录信息已失效，无法保存')
    return
  }
  persistPlanToStorage()
  ElMessage.success('菜谱计划已保存，下次登录可继续修改')
}

// 从localStorage加载菜谱计划
const loadSavedPlan = () => {
  if (!authStore.user?.id) return
  const storageKey = `recipePlan_user_${authStore.user.id}`
  const savedPlan = localStorage.getItem(storageKey)
  if (savedPlan) {
    try {
      const planData = JSON.parse(savedPlan)
      customDishes.value = planData.customDishes || []
      recipePlan.value = planData.recipePlan || []
      mealSummaries.value = planData.mealSummaries || {}
      if (planData.rulesForm) {
        Object.assign(rulesForm, planData.rulesForm)
      }
      if (Array.isArray(planData.availableIngredients)) {
        availableIngredients.value = planData.availableIngredients
      }
      if (planData.ingredientPrices && typeof planData.ingredientPrices === 'object') {
        ingredientPrices.value = planData.ingredientPrices
      }
      procurementSaved.value = Array.isArray(planData.procurementSaved) ? planData.procurementSaved : null
      hasSavedPlan.value = true
      ElMessage.info('已加载未完成的菜谱计划')
    } catch (error) {
      console.error('加载保存的菜谱计划失败:', error)
      localStorage.removeItem(storageKey)
    }
  }
}

// 发布菜谱计划 — 一次性提交整份计划到后端
const publishPlan = () => {
  const run = async () => {
    const all = [...customDishes.value, ...recipePlan.value]
    if (all.length === 0) {
      ElMessage.warning('当前没有可发布的菜谱')
      return
    }
    const loadingInstance = ElLoading.service({ lock: true, text: '正在发布菜谱计划...', background: 'rgba(0, 0, 0, 0.7)' })
    try {
      const planDateCandidates = normalizeAndSortDates(
        all.map((r: any) => r?.apply_date).filter((v: any) => typeof v === 'string' && v)
      )
      const planDateYMD = planDateCandidates[0] || getPlanDates()[0] || tomorrowYMD

      const meals = all.map((row: any) => ({
        id: row.id && String(row.id).startsWith('custom-') ? undefined : row.id,
        dish_id: typeof row.id === 'number' ? row.id : undefined,
        day: row.day ? Number(row.day) : undefined,
        apply_date: row.apply_date || (row.day ? getApplyDateForDay(row.day) : undefined),
        name: row.name || `计划菜品${row.day || ''}${row.time || ''}`,
        meal_type: row.time || '早餐',
        dish_type: row.dish_type || '',
        category: row.category || '',
        servings: Number(row.servings) || 1,
        nutrition: row.nutrition || '',
        dish_recipe: row.description || row.dish_recipe || '',
        ingredients: row.ingredients || '',
        flavor: row.flavor || '',
        season: row.season || '',
        cost_price: row.cost_price || 0
      }))
      const procurementForPublish = (procurementSaved.value && procurementSaved.value.length > 0) ? procurementSaved.value : procurementRows.value
      
      // 添加团餐营养总结
      if (adminDiningStyle.value === '团餐' && mealSummaries.value) {
        Object.entries(mealSummaries.value).forEach(([key, summary]) => {
          const [day, mealKey] = key.split('_')
          meals.push({
            name: `营养总结_${day}_${mealKey}`,
            meal_type: '__summary__',
            day: Number(day),
            nutrition_summary: summary
          })
        })
      }

      meals.push({
        name: '配方采购表',
        meal_type: '__procurement__',
        servings: 1,
        procurement_rows: (procurementForPublish || []).map((r: any) => ({
          ingredient: String(r?.ingredient || '').trim(),
          total_grams: Number(r?.total_grams) || 0
        })).filter((r: any) => r.ingredient)
      })

      // 计算各餐次的平均成本
      let breakfastCost = 0, lunchCost = 0, dinnerCost = 0
      let breakfastCount = 0, lunchCount = 0, dinnerCount = 0
      
      meals.forEach(meal => {
        if (meal.meal_type === '早餐') {
          breakfastCost += (Number(meal.cost_price) || 0) * (Number(meal.servings) || 1)
          breakfastCount++
        } else if (meal.meal_type === '午餐') {
          lunchCost += (Number(meal.cost_price) || 0) * (Number(meal.servings) || 1)
          lunchCount++
        } else if (meal.meal_type === '晚餐') {
          dinnerCost += (Number(meal.cost_price) || 0) * (Number(meal.servings) || 1)
          dinnerCount++
        }
      })
      
      const breakfast_avg_cost = breakfastCount > 0 ? breakfastCost / breakfastCount : 0
      const lunch_avg_cost = lunchCount > 0 ? lunchCost / lunchCount : 0
      const dinner_avg_cost = dinnerCount > 0 ? dinnerCost / dinnerCount : 0
      
      const payload = {
        name: `菜谱计划_${planDateYMD}`,
        date: planDateYMD,
        age_group: authStore.user?.age_group || 'primary',
        total_cost: Number(totalPlanCost.value),
        breakfast_avg_cost: breakfast_avg_cost,
        lunch_avg_cost: lunch_avg_cost,
        dinner_avg_cost: dinner_avg_cost,
        meals
      }

      const result = await recStore.publishMealPlan(payload)
      ElMessage.success(`菜谱计划发布成功`)
      
      // 发布成功后，调用 AI 分析
      if (result && result.id) {
        analyzePlanWithAI(meals, result.id)
      }

      // 发布成功后，删除当前用户特定的存储项
      if (authStore.user?.id) {
        localStorage.removeItem(`recipePlan_user_${authStore.user.id}`)
      }
    } catch (error: any) {
      console.error('发布菜谱计划失败:', error)
      ElMessage.error(error?.response?.data?.detail || error?.message || '发布失败')
    } finally {
      loadingInstance.close()
    }
  }
  run()
}



// 添加自定义菜品
const addCustomDish = () => {
  customDishes.value.push({
    id: `custom-${Date.now()}`,
    day: 1,
    apply_date: getApplyDateForDay(1),
    time: '午餐',
    name: '自定义菜品',
    dish_type: '素菜类',
    category: '素菜类',
    flavor: '原味',
    season: getCurrentSeason(),
    description: '',
    nutrition: '卡路里：0 kcal，蛋白质：0 g，脂肪：0 g，碳水化合物：0 g',
    servings: rulesForm.servings,
    is_custom: true
  })
}

// 辅助函数
const normalizeText = (s: string) => (s || '').replace(/\s+/g, '').toLowerCase()

// 删除菜品
const deleteDish = (index: number) => {
  if (index < customDishes.value.length) {
    customDishes.value.splice(index, 1)
  } else {
    const recipeIndex = index - customDishes.value.length
    recipePlan.value.splice(recipeIndex, 1)
  }
  ElMessage.success('菜品已删除')
}

const deleteMeal = (day: number, mealType: string) => {
  const before = recipePlan.value.length
  recipePlan.value = recipePlan.value.filter(d => !(Number(d.day) === Number(day) && String(d.time) === mealType))
  
  // 清除对应的营养总结
  const mealKey = dishTypeToBackend(mealType)
  const summaryKey = `${day}_${mealKey}`
  if (mealSummaries.value[summaryKey]) {
    delete mealSummaries.value[summaryKey]
  }

  if (recipePlan.value.length !== before) ElMessage.success('已清空该餐次菜品')
}

const deleteMealDish = (dish: any) => {
  if (!dish) return
  const day = Number(dish.day)
  const time = String(dish.time)
  const id = dish.id
  const before = recipePlan.value.length
  recipePlan.value = recipePlan.value.filter(d => {
    if (Number(d.day) !== day) return true
    if (String(d.time) !== time) return true
    return d.id !== id
  })

  // 清除对应的营养总结（因为餐次内容已变）
  const mealKey = dishTypeToBackend(time)
  const summaryKey = `${day}_${mealKey}`
  if (mealSummaries.value[summaryKey]) {
    delete mealSummaries.value[summaryKey]
  }

  if (recipePlan.value.length !== before) ElMessage.success('菜品已删除')
}

// 获取营养指标名称
const getNutrientName = (key: string) => {
  const names: Record<string, string> = {
    total_calories: '能量(kcal)',
    total_protein: '蛋白质(g)',
    total_fat: '脂肪(g)',
    total_carbohydrates: '碳水化合物(g)',
    total_calcium: '钙(mg)',
    total_iron: '铁(mg)',
    total_vitamin_c: '维生素C(mg)',
    // 同时支持不带 total_ 前缀的旧格式
    calcium: '钙(mg)',
    iron: '铁(mg)',
    zinc: '锌(mg)',
    vitamin_a: '维生素A(μgRE)',
    vitamin_b1: '维生素B1(mg)',
    vitamin_b2: '维生素B2(mg)',
    vitamin_c: '维生素C(mg)'
  }
  return names[key] || key
}

// 兼容两种摘要结构：传统营养达标(summary.is_compliant) 与 加权评分(summary.weighted_score)
const isWeightedSummary = (summary: any) => {
  if (!summary) return false
  const keys = ['weighted_score', 'nutrition_score', 'cost_score', 'variety_score']
  return keys.some((k) => summary[k] !== undefined && summary[k] !== null && !Number.isNaN(Number(summary[k])))
}

const getSummaryTagType = (summary: any) => {
  if (!summary) return 'info'
  if (isWeightedSummary(summary)) {
    const s = toScore(summary.weighted_score)
    if (s >= 85) return 'success'
    if (s >= 70) return 'warning'
    return 'danger'
  }
  return summary.is_compliant ? 'success' : 'danger'
}

const getSummaryTagText = (summary: any) => {
  if (!summary) return '-'
  if (isWeightedSummary(summary)) {
    const s = toScore(summary.weighted_score)
    if (s >= 85) return '优秀'
    if (s >= 70) return '良好'
    return '待优化'
  }
  return summary.is_compliant ? '达标' : '待调整'
}

const toScore = (v: any): number => {
  const n = Number(v)
  if (Number.isNaN(n)) return 0
  return n
}

const flattenedRows = computed(() => {
  const rows: any[] = []
  groupedRows.value.forEach(dayPlan => {
    // 按 早餐、午餐、晚餐 顺序处理
    const mealTypes = ['早餐', '午餐', '晚餐']
    mealTypes.forEach(mealType => {
      // 仅处理用户选择展示的餐饮类型
      if (!rulesForm.dishType.includes(mealType)) return

      const mealKey = mealType === '早餐' ? 'breakfast' : (mealType === '午餐' ? 'lunch' : 'dinner')
      const dishes = dayPlan[mealKey] || []
      
      if (dishes.length === 0) {
        // 占位行：当该餐次没有菜品时，显示一行
        rows.push({
          day: dayPlan.day,
          apply_date: dayPlan.apply_date,
          mealType: mealType,
          isPlaceholder: true,
          dish: null,
          summary: mealSummaries.value[`${dayPlan.day}_${mealKey}`] || null
        })
      } else {
        dishes.forEach((dish: any, index: number) => {
          rows.push({
            day: dayPlan.day,
            apply_date: dayPlan.apply_date,
            mealType: mealType,
            isPlaceholder: false,
            dish: dish,
            summary: mealSummaries.value[`${dayPlan.day}_${mealKey}`] || null,
            isFirstInMeal: index === 0,
            mealRowCount: dishes.length
          })
        })
      }
    })
  })

  // 计算合并单元格所需的 span 计数
  // 1. 计算每个 Day 包含的总行数
  const dayCounts: Record<number, number> = {}
  rows.forEach(r => {
    dayCounts[r.day] = (dayCounts[r.day] || 0) + 1
  })

  // 2. 计算每个 Day + MealType 包含的总行数
  const mealCounts: Record<string, number> = {}
  rows.forEach(r => {
    const key = `${r.day}-${r.mealType}`
    mealCounts[key] = (mealCounts[key] || 0) + 1
  })

  // 3. 将计数填回 rows，仅在合并单元格的第一行设置 > 0 的值
  const seenDay = new Set()
  const seenMeal = new Set()
  
  rows.forEach(r => {
    const mealKey = `${r.day}-${r.mealType}`
    
    if (!seenDay.has(r.day)) {
      r.daySpan = dayCounts[r.day]
      seenDay.add(r.day)
    } else {
      r.daySpan = 0
    }

    if (!seenMeal.has(mealKey)) {
      r.mealSpan = mealCounts[mealKey]
      seenMeal.add(mealKey)
    } else {
      r.mealSpan = 0
    }
  })

  return rows
})

// 推荐方案解释（基于 mealSummaries：加权评分的 nutrition/cost/variety）
const weightedExplanationOverall = computed(() => {
  const summaries = Object.values(mealSummaries.value || {}).filter(
    (s: any) => s && typeof s.weighted_score === 'number'
  )
  if (summaries.length === 0) return null

  const avg = (k: string) => {
    return summaries.reduce((sum: number, s: any) => sum + Number(s?.[k] || 0), 0) / summaries.length
  }

  const avgWeightedScore = avg('weighted_score')
  const avgNutritionScore = avg('nutrition_score')
  const avgCostScore = avg('cost_score')
  const avgVarietyScore = avg('variety_score')

  const maxVal = Math.max(avgNutritionScore, avgCostScore, avgVarietyScore)
  let primaryKey = '营养'
  if (maxVal === avgCostScore) primaryKey = '成本'
  else if (maxVal === avgVarietyScore) primaryKey = '多样性'

  const labelMap: Record<string, string> = {
    '营养': '营养更贴目标区间',
    '成本': '成本更符合预算控制',
    '多样性': '食材覆盖更均衡更丰富'
  }

  return {
    avgWeightedScore,
    avgNutritionScore,
    avgCostScore,
    avgVarietyScore,
    primaryAdvantageLabel: labelMap[primaryKey] || '综合更优'
  }
})

// 不再展示逐餐次明细：仅展示方案总评分（保留 weightedExplanationOverall 即可）

const objectSpanMethod = ({ row, columnIndex }: any) => {
  // 1. 时间列 (index 0)
  if (columnIndex === 0) {
    return {
      rowspan: row.daySpan,
      colspan: row.daySpan > 0 ? 1 : 0
    }
  }
  // 2. 餐饮类型列 (index 1)
  if (columnIndex === 1) {
    return {
      rowspan: row.mealSpan,
      colspan: row.mealSpan > 0 ? 1 : 0
    }
  }
  
  // 3. 类型 (index 2) 和 4. 菜品详情 (index 3) 都不合并，每行显示一个菜品
  
  // 团餐模式下的特殊处理
  if (adminDiningStyle.value === '团餐') {
    // 5. 营养评估列 (index 4)
    if (columnIndex === 4) {
      return {
        rowspan: row.mealSpan,
        colspan: row.mealSpan > 0 ? 1 : 0
      }
    }
    // 6. 餐次管理列 (index 5)
    if (columnIndex === 5) {
      return {
        rowspan: row.mealSpan,
        colspan: row.mealSpan > 0 ? 1 : 0
      }
    }
  } else {
    // 非团餐模式下，餐次管理列是 index 4
    if (columnIndex === 4) {
      return {
        rowspan: row.mealSpan,
        colspan: row.mealSpan > 0 ? 1 : 0
      }
    }
  }
  
  return {
    rowspan: 1,
    colspan: 1
  }
}

const handleEditDish = (dish: any) => {
  if (!dish) return
  currentDish.value = JSON.parse(JSON.stringify(dish))
  editIndex.value = recipePlan.value.findIndex(d => String(d.time) === String(dish.time) && Number(d.day) === Number(dish.day) && d.id === dish.id)
  editDialogVisible.value = true
}

const saveEditedDish = () => {
  if (!currentDish.value) return
  if (editIndex.value >= 0) {
    const next = { ...currentDish.value }
    if (!next.apply_date) {
      next.apply_date = getApplyDateForDay(next.day)
    } else {
      next.apply_date = getApplyDateForDay(next.day) || next.apply_date
    }
    recipePlan.value[editIndex.value] = next
  }
  ElMessage.success('已更新菜品信息')
  editDialogVisible.value = false
}



</script>

<style scoped>
.dialog-action-buttons {
  display: flex;
  justify-content: center;
  gap: 8px;
}

.meal-edit-dialog :deep(.el-dialog__body) {
  padding: 10px 20px;
}

.meal-edit-dialog :deep(.el-table) {
  margin-bottom: 0;
}

/* 横向布局专用样式 */

.horizontal-layout {
  margin-top: 20px;
}

.meal-type-cell {
  padding: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.meal-type-name {
  font-size: 18px;
  font-weight: 800;
  color: #303133;
  padding: 4px 12px;
  background: #f0f2f5;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
}

.meal-actions-vertical {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.meal-actions-vertical :deep(.el-button) {
  margin-left: 0 !important;
  justify-content: center;
  font-weight: 500;
  font-size: 12px;
  padding: 5px 8px;
  border-radius: 6px;
}

/* 餐次管理：浅色按钮（避免高饱和主色） */
.meal-actions-vertical :deep(.meal-btn-edit) {
  background-color: #faf6f0 !important;
  border-color: #e8e0d6 !important;
  color: #8b7355 !important;
}
.meal-actions-vertical :deep(.meal-btn-edit:hover),
.meal-actions-vertical :deep(.meal-btn-edit:focus) {
  background-color: #f3ebe0 !important;
  border-color: #ddd2c4 !important;
  color: #6b5a45 !important;
}

.meal-actions-vertical :deep(.meal-btn-add) {
  background-color: #f4f7fb !important;
  border-color: #dce4ee !important;
  color: #5a7a9e !important;
}
.meal-actions-vertical :deep(.meal-btn-add:hover),
.meal-actions-vertical :deep(.meal-btn-add:focus) {
  background-color: #e8eef6 !important;
  border-color: #c9d6e8 !important;
  color: #4a6585 !important;
}

.meal-actions-vertical :deep(.meal-btn-regen) {
  background-color: #f5f6f8 !important;
  border-color: #e2e4e8 !important;
  color: #6b7280 !important;
}
.meal-actions-vertical :deep(.meal-btn-regen:hover),
.meal-actions-vertical :deep(.meal-btn-regen:focus) {
  background-color: #ebecef !important;
  border-color: #d1d5db !important;
  color: #4b5563 !important;
}

.meal-actions-vertical :deep(.meal-btn-clear) {
  background-color: #fdf5f5 !important;
  border-color: #f0dede !important;
  color: #b87a7a !important;
}
.meal-actions-vertical :deep(.meal-btn-clear:hover:not(.is-disabled)),
.meal-actions-vertical :deep(.meal-btn-clear:focus:not(.is-disabled)) {
  background-color: #f8eaea !important;
  border-color: #e5cfcf !important;
  color: #9a6565 !important;
}
.meal-actions-vertical :deep(.meal-btn-clear.is-disabled) {
  opacity: 0.45;
}

/* 修改弹窗：复用餐次管理同款浅色按钮样式 */
.meal-edit-dialog :deep(.meal-btn-edit) {
  background-color: #faf6f0 !important;
  border-color: #e8e0d6 !important;
  color: #8b7355 !important;
}
.meal-edit-dialog :deep(.meal-btn-edit:hover),
.meal-edit-dialog :deep(.meal-btn-edit:focus) {
  background-color: #f3ebe0 !important;
  border-color: #ddd2c4 !important;
  color: #6b5a45 !important;
}

.meal-edit-dialog :deep(.meal-btn-regen) {
  background-color: #f5f6f8 !important;
  border-color: #e2e4e8 !important;
  color: #6b7280 !important;
}
.meal-edit-dialog :deep(.meal-btn-regen:hover),
.meal-edit-dialog :deep(.meal-btn-regen:focus) {
  background-color: #ebecef !important;
  border-color: #d1d5db !important;
  color: #4b5563 !important;
}

.meal-edit-dialog :deep(.meal-btn-clear) {
  background-color: #fdf5f5 !important;
  border-color: #f0dede !important;
  color: #b87a7a !important;
}
.meal-edit-dialog :deep(.meal-btn-clear:hover),
.meal-edit-dialog :deep(.meal-btn-clear:focus) {
  background-color: #f8eaea !important;
  border-color: #e5cfcf !important;
  color: #9a6565 !important;
}

.dish-detail-horizontal {
  padding: 8px 12px;
}

.dish-actions-cell {
  display: flex;
  justify-content: center;
  gap: 10px;
}

.action-btn-styled {
  font-weight: 800 !important;
  padding: 6px 16px !important;
  border-radius: 6px !important;
  transition: all 0.2s !important;
}

.action-btn-styled:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.empty-placeholder {
  padding: 20px;
  text-align: center;
  color: #909399;
  font-style: italic;
  background: #fafafa;
  border-radius: 4px;
}

/* 加载状态美化 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
  margin: 20px 0;
}

.loading-icon {
  font-size: 40px;
  color: #409eff;
  margin-bottom: 16px;
  animation: rotate 2s linear infinite;
}

.loading-container p {
  color: #606266;
  font-size: 16px;
  margin-bottom: 24px;
}

.loading-progress-wrapper {
  width: 100%;
  max-width: 500px;
  margin: 0 auto;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 全局容器优化 */
.recommendation-container {
  padding: 16px 24px;
  max-width: 1400px;
  margin: 0 auto;
  background-color: #f5f7fa;
  min-height: 100vh;
}

/* 页面头部美化 */
.page-header {
  margin-bottom: 20px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fb 100%);
  padding: 20px 30px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.8);
}

.title-section h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #1a1a1a;
  letter-spacing: -0.5px;
}

.subtitle {
  margin: 6px 0 0;
  color: #606266;
  font-size: 14px;
  opacity: 0.8;
}

/* 卡片通用样式 */
.custom-dishes-section, .rules-section, .results-section {
  background: white;
  padding: 20px 24px;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
  margin-bottom: 20px;
  border: 1px solid #f0f2f5;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.custom-dishes-section:hover, .rules-section:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
}

h3 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 10px;
}

h3::before {
  content: '';
  width: 4px;
  height: 18px;
  background: #409eff;
  border-radius: 2px;
}

/* 食材输入美化 */
.custom-dishes-container {
  background: #f8f9fb;
  padding: 16px;
  border-radius: 10px;
  border: 1px dashed #dcdfe6;
}

/* 表单元素美化 */
:deep(.el-form-item) {
  margin-bottom: 16px;
}

:deep(.el-form-item__label) {
  font-weight: 600;
  color: #606266;
  padding-bottom: 4px;
}

:deep(.el-input__wrapper), :deep(.el-select__wrapper) {
  box-shadow: 0 0 0 1px #dcdfe6 inset !important;
  border-radius: 6px;
  padding: 2px 12px;
  transition: all 0.2s;
}

:deep(.el-input__wrapper:hover), :deep(.el-select__wrapper:hover) {
  box-shadow: 0 0 0 1px #409eff inset !important;
}

/* 按钮美化 */
.form-actions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f2f5;
  display: flex;
  justify-content: center;
  gap: 16px;
}

.el-button--large {
  padding: 10px 28px;
  font-weight: 600;
  border-radius: 8px;
  letter-spacing: 0.5px;
}

/* 结果区域美化 */
.plan-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  background: #f8f9fb;
  padding: 12px;
  border-radius: 10px;
  margin-bottom: 16px;
}

/* 表格视觉升级 */
.recipe-plan-table {
  overflow: hidden;
  border-radius: 12px;
  border: 1px solid #ebeef5;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.02);
}

.csv-style-table :deep(.el-table__header-wrapper th) {
  background-color: #f8f9fb !important;
  font-weight: 700;
  color: #303133;
  height: 54px;
}

/* 每一天行之间的高亮分界线 */
.csv-style-table :deep(.el-table__row) {
  border-bottom: 8px solid #f0f2f5;
}

/* 时间列（第一列）的特殊背景，增强视觉锚点 */
.csv-style-table :deep(.el-table__row td:first-child) {
  background-color: #f8f9fb !important;
  border-right: 2px solid #e4e7ed;
}

/* 鼠标悬停时取消分界线的变色，保持清晰度 */
.csv-style-table :deep(.el-table__row:hover > td) {
  background-color: inherit !important;
}

/* 天数单元格卡片感 */
.day-cell {
  padding: 6px 10px;
}

.day-cell-title {
  font-size: 16px;
  color: #409eff;
  margin-bottom: 2px;
}

.day-cell-date {
  background: #ffffff;
  padding: 2px 8px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  color: #909399;
  font-size: 12px;
}

/* 菜品表格内部美化 */
.meal-dish-table {
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  margin: 4px 8px;
  width: calc(100% - 16px) !important;
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

.clickable-dish-name {
  font-size: 14px;
  color: #2c3e50;
  border-bottom: 1px dashed #dcdfe6;
  padding-bottom: 1px;
  cursor: pointer;
  transition: all 0.2s;
}

.clickable-dish-name:hover {
  color: #409eff;
  border-bottom-color: #409eff;
}

.dish-name-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.dish-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.servings-text {
  font-size: 12px;
  color: #67c23a;
  background: #f0f9eb;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 600;
  border: 1px solid #e1f3d8;
}

/* 底部操作区 */
.meal-footer-actions {
  padding: 8px 12px;
  background: #ffffff;
  border-top: 1px solid #f0f2f5;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.meal-footer-actions :deep(.el-button) {
  font-weight: bold;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.dish-actions {
  margin-top: 8px;
  display: flex;
  gap: 6px;
  justify-content: flex-end;
}

.dish-actions :deep(.el-button) {
  font-weight: 700;
  padding: 4px 10px;
  height: 28px;
  letter-spacing: 0.5px;
  transition: all 0.2s;
}

/* 提高按钮对比度 */
.dish-actions :deep(.el-button--primary) {
  background-color: #409eff !important;
  border-color: #409eff !important;
  color: #ffffff !important;
  font-weight: 800 !important;
}

.dish-actions :deep(.el-button--danger) {
  background-color: #f56c6c !important;
  border-color: #f56c6c !important;
  color: #ffffff !important;
  font-weight: 800 !important;
}

.dish-actions :deep(.el-button--primary:hover) {
  background-color: #66b1ff !important;
  border-color: #66b1ff !important;
  box-shadow: 0 0 8px rgba(64, 158, 255, 0.4);
}

.dish-actions :deep(.el-button--danger:hover) {
  background-color: #f78989 !important;
  border-color: #f78989 !important;
  box-shadow: 0 0 8px rgba(245, 108, 108, 0.4);
}

.meal-footer-actions :deep(.el-button) {
  font-weight: 800 !important;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  letter-spacing: 0.5px;
  padding: 8px 15px;
  height: 32px;
}

.meal-footer-actions :deep(.el-button--primary) {
  background-color: #409eff !important;
  border-color: #409eff !important;
  color: #ffffff !important;
}

.meal-footer-actions :deep(.el-button--info) {
  background-color: #606266 !important;
  border-color: #606266 !important;
  color: #ffffff !important;
}

.meal-footer-actions :deep(.el-button--danger) {
  background-color: #f56c6c !important;
  border-color: #f56c6c !important;
  color: #ffffff !important;
}

.meal-footer-actions :deep(.el-button:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 顶部生成按钮增强 */
.form-actions :deep(.el-button--primary) {
  background-color: #409eff !important;
  border-color: #409eff !important;
  font-weight: 800 !important;
  font-size: 16px;
  height: 44px;
}

.form-actions :deep(.el-button--primary:hover) {
  background-color: #66b1ff !important;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

/* 空状态美化 */
.empty-container {
  padding: 80px 40px;
  background: white;
  border-radius: 16px;
  text-align: center;
}

:deep(.el-empty__description) {
  margin-top: 20px;
  font-size: 16px;
  color: #909399;
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .recommendation-container {
    padding: 16px;
  }
  .el-col {
    margin-bottom: 16px;
  }
}


.empty-meal-slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px 0;
  border: 1px dashed #dcdfe6;
  border-radius: 8px;
  background: #fcfcfc;
  transition: all 0.3s;
  margin-bottom: 8px;
}

.empty-meal-slot:hover {
  border-color: #409eff;
  background: #f5f7fa;
}

.add-dish-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
  border-radius: 20px;
  padding: 8px 16px;
}

.add-dish-btn :deep(.el-icon) {
  font-size: 14px;
}

.search-item-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 4px 0;
}

.search-item-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-item-name {
  font-weight: 600;
  color: #303133;
}

.search-item-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-item-calories {
  font-size: 12px;
  color: #909399;
  min-width: 60px;
  text-align: right;
}

.dish-search-option {
  height: auto !important;
  line-height: normal !important;
  padding: 8px 12px !important;
}

.confirm-add-btn {
  padding: 10px 24px;
  font-weight: 600;
  border-radius: 6px;
}
/* 推荐方案解释区块（放在推荐菜品表格下方） */
.plan-explain-section {
  margin-top: 16px;
  padding: 16px 18px;
  background: #ffffff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.02);
}

.plan-explain-title {
  margin: 0 0 10px;
  font-size: 16px;
  font-weight: 800;
  color: #303133;
}

.plan-explain-overall {
  font-size: 13px;
  color: #4b5563;
  margin-bottom: 12px;
  line-height: 1.6;
}

.plan-explain-strong {
  color: #409eff;
  font-weight: 900;
}

.plan-explain-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.plan-explain-item {
  padding: 12px;
  background: #f8f9fb;
  border: 1px solid #f0f2f5;
  border-radius: 10px;
}

.plan-explain-item-header {
  font-weight: 800;
  color: #303133;
  margin-bottom: 6px;
}

.plan-explain-item-body {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.7;
}
/* 配方采购表：删除按钮（浅色、小尺寸，避免太深） */
.procurement-btn-delete {
  background-color: #fff9f9 !important;
  border-color: #f3e0e0 !important;
  color: #aa6b6b !important;
  padding: 0 8px !important;
  height: 24px !important;
  font-size: 11px !important;
  border-radius: 6px !important;
}
.procurement-btn-delete:hover,
.procurement-btn-delete:focus {
  background-color: #ffecec !important;
  border-color: #f0cfcf !important;
  color: #955c5c !important;
}

/* 兜底：覆盖 Element Plus danger/plain 的更高优先级样式 */
:deep(.procurement-btn-delete) {
  background-color: #fff9f9 !important;
  border-color: #f3e0e0 !important;
  color: #aa6b6b !important;
}
:deep(.procurement-btn-delete:hover),
:deep(.procurement-btn-delete:focus) {
  background-color: #ffecec !important;
  border-color: #f0cfcf !important;
  color: #955c5c !important;
}

/* 配方采购表：预计成本文字（浅色，避免突兀） */
.procurement-cost-text {
  color: #b77979 !important;
  font-weight: 600 !important;
}

.procurement-total-cost-text {
  font-size: 18px;
  font-weight: bold;
  color: #b77979 !important;
}

</style>

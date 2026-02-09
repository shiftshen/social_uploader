<template>
  <div class="publish-center">
    <!-- Tab管理区域 -->
    <div class="tab-management">
      <div class="tab-header">
        <div class="tab-list">
          <div 
            v-for="tab in tabs" 
            :key="tab.name"
            :class="['tab-item', { active: activeTab === tab.name }]"
            @click="activeTab = tab.name"
          >
            <span>{{ tab.label }}</span>
            <el-icon 
              v-if="tabs.length > 1"
              class="close-icon" 
              @click.stop="removeTab(tab.name)"
            >
              <Close />
            </el-icon>
          </div>
        </div>
        <div class="tab-actions">
          <el-button 
            type="primary" 
            size="small" 
            @click="addTab"
            class="add-tab-btn"
          >
            <el-icon><Plus /></el-icon>
            添加Tab
          </el-button>
          <el-button 
            type="success" 
            size="small" 
            @click="batchPublish"
            :loading="batchPublishing"
            class="batch-publish-btn"
          >
            批量发布
          </el-button>
        </div>
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="publish-content">
      <div class="tab-content-wrapper">
        <div 
          v-for="tab in tabs" 
          :key="tab.name"
          v-show="activeTab === tab.name"
          class="tab-content"
        >
          <!-- 发布状态提示 -->
          <div v-if="tab.publishStatus" class="publish-status">
            <el-alert
              :title="tab.publishStatus.message"
              :type="tab.publishStatus.type"
              :closable="false"
              show-icon
            />
          </div>

          <!-- 视频上传区域 -->
          <div class="upload-section">
            <div class="section-header">
              <h3>素材库</h3>
              <el-upload
                class="inline-upload"
                :action="`${apiBaseUrl}/upload`"
                :on-success="(response, file) => handleUploadSuccess(response, file, tab)"
                :on-error="handleUploadError"
                multiple
                :show-file-list="false"
                accept="video/*"
                :headers="authHeaders"
              >
                <el-button type="primary" size="small">
                  <el-icon><Upload /></el-icon>
                  上传新视频
                </el-button>
              </el-upload>
            </div>
            
            <!-- 素材列表 -->
            <div class="material-selection-area">
              <div v-if="loadingMaterials" class="loading-placeholder">
                <el-icon class="is-loading"><Loading /></el-icon> 加载中...
              </div>
              <div v-else-if="materials.length === 0" class="empty-placeholder">
                暂无素材，请点击右上角上传
              </div>
              <el-checkbox-group v-else v-model="tab.selectedMaterialIds" @change="(val) => handleMaterialSelectionChange(val, tab)">
                <div class="material-grid">
                  <div
                    v-for="material in displayedMaterials"
                    :key="material.id"
                    class="material-card"
                    :class="{ 'is-selected': tab.selectedMaterialIds.includes(material.id) }"
                  >
                    <el-checkbox :label="material.id" class="material-checkbox">
                      <span class="material-name" :title="material.filename">{{ material.filename }}</span>
                    </el-checkbox>
                    <div class="material-meta">
                      <span class="file-size">{{ material.filesize }}MB</span>
                      <span class="upload-time">{{ formatTime(material.upload_time) }}</span>
                    </div>
                  </div>
                </div>
              </el-checkbox-group>
              
              <!-- 分页 -->
              <div class="pagination-wrapper" v-if="materials.length > 5">
                <el-pagination
                  v-model:current-page="currentPage"
                  :page-size="5"
                  layout="prev, pager, next"
                  :total="materials.length"
                  @current-change="handlePageChange"
                  small
                />
              </div>
            </div>

            <!-- 已选文件预览 (仅显示已选中的) -->
            <div v-if="tab.fileList.length > 0" class="selected-files-preview">
              <h4>已选视频 ({{ tab.fileList.length }})：</h4>
              <div class="file-list">
                <div v-for="(file, index) in tab.fileList" :key="index" class="file-item">
                  <el-link :href="file.url" target="_blank" type="primary">{{ file.name }}</el-link>
                  <el-button type="text" class="remove-btn" @click="deselectMaterial(tab, file.path)">
                    <el-icon><Close /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>

          <!-- 上传选项弹窗 (已废弃) -->

          <!-- 本地上传弹窗 (已废弃) -->

          <!-- 批量发布进度对话框 -->
          <el-dialog
            v-model="batchPublishDialogVisible"
            title="批量发布进度"
            width="500px"
            :close-on-click-modal="false"
            :close-on-press-escape="false"
            :show-close="false"
          >
            <div class="publish-progress">
              <el-progress 
                :percentage="publishProgress"
                :status="publishProgress === 100 ? 'success' : ''"
              />
              <div v-if="currentPublishingTab" class="current-publishing">
                正在发布：{{ currentPublishingTab.label }}
              </div>
              
              <!-- 发布结果列表 -->
              <div class="publish-results" v-if="publishResults.length > 0">
                <div 
                  v-for="(result, index) in publishResults" 
                  :key="index"
                  :class="['result-item', result.status]"
                >
                  <el-icon v-if="result.status === 'success'"><Check /></el-icon>
                  <el-icon v-else-if="result.status === 'error'"><Close /></el-icon>
                  <el-icon v-else><InfoFilled /></el-icon>
                  <span class="label">{{ result.label }}</span>
                  <span class="message">{{ result.message }}</span>
                </div>
              </div>
            </div>
            
            <template #footer>
              <div class="dialog-footer">
                <el-button 
                  @click="cancelBatchPublish" 
                  :disabled="publishProgress === 100"
                >
                  取消发布
                </el-button>
                <el-button 
                  type="primary" 
                  @click="batchPublishDialogVisible = false"
                  v-if="publishProgress === 100"
                >
                  关闭
                </el-button>
              </div>
            </template>
          </el-dialog>

          <!-- 素材库选择弹窗 (已废弃) -->

          <!-- 平台选择 -->
          <div class="platform-section">
            <h3>平台</h3>
            <el-radio-group v-model="tab.selectedPlatform" class="platform-radios">
              <el-radio 
                v-for="platform in platforms" 
                :key="platform.key"
                :label="platform.key"
                class="platform-radio"
              >
                {{ platform.name }}
              </el-radio>
            </el-radio-group>
          </div>

          <!-- 账号选择 -->
          <div class="account-section">
            <h3>账号</h3>
            <div class="account-display">
              <div class="selected-accounts">
                <el-tag
                  v-for="(account, index) in tab.selectedAccounts"
                  :key="index"
                  closable
                  @close="removeAccount(tab, index)"
                  class="account-tag"
                >
                  {{ getAccountDisplayName(account) }}
                </el-tag>
              </div>
              <el-button 
                type="primary" 
                plain 
                @click="openAccountDialog(tab)"
                class="select-account-btn"
              >
                选择账号
              </el-button>
            </div>
          </div>

          <!-- 账号选择弹窗 -->
          <el-dialog
            v-model="accountDialogVisible"
            title="选择账号"
            width="600px"
            class="account-dialog"
          >
            <div class="account-dialog-content">
              <el-checkbox-group v-model="tempSelectedAccounts">
                <div class="account-list">
                  <el-checkbox
                    v-for="account in availableAccounts"
                    :key="account.id"
                    :label="account.id"
                    class="account-item"
                  >
                    <div class="account-info">
                      <span class="account-name">{{ account.name }}</span>                      
                    </div>
                  </el-checkbox>
                </div>
              </el-checkbox-group>
            </div>

            <template #footer>
              <div class="dialog-footer">
                <el-button @click="accountDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="confirmAccountSelection">确定</el-button>
              </div>
            </template>
          </el-dialog>

          <!-- 标题输入 -->
          <div class="title-section">
            <div class="section-header">
              <h3>标题</h3>
              <el-button
                type="primary"
                plain
                size="small"
                class="ai-generate-btn"
                :loading="tab.aiTitleLoading"
                @click="requestAiTitle(tab)"
              >
                AI生成
              </el-button>
            </div>
            <el-input
              v-model="tab.title"
              type="textarea"
              :rows="3"
              placeholder="请输入标题"
              maxlength="100"
              show-word-limit
              class="title-input"
            />

            <div
              v-if="tab.selectedPlatform === 1"
              class="xhs-title-section"
            >
              <div class="xhs-title-header">
                <span>小红书专用标题（≤20个字符）</span>
                <el-button
                  type="primary"
                  plain
                  size="small"
                  :loading="tab.aiXhsTitleLoading"
                  @click="requestAiXhsTitle(tab)"
                >
                  AI生成
                </el-button>
              </div>
              <el-input
                v-model="tab.xhsTitle"
                type="textarea"
                :rows="2"
                placeholder="请输入不超过20个字符的小红书标题"
                maxlength="20"
                show-word-limit
                class="xhs-title-input"
              />
              <p class="xhs-title-hint">建议控制在20个中文字符以内，超出部分发布时将被截断。</p>
            </div>
          </div>

          <!-- 话题输入 -->
          <div class="topic-section">
            <div class="section-header">
              <h3>话题</h3>
              <el-button
                type="primary"
                plain
                size="small"
                class="ai-generate-btn"
                :loading="tab.aiTopicLoading"
                @click="requestAiTopics(tab)"
              >
                AI生成
              </el-button>
            </div>
            <div class="topic-display">
              <el-input
                v-model="tab.topicInputValue"
                type="textarea"
                :rows="3"
                placeholder="请输入话题，多个话题请用空格分隔，例如：#游戏 #精彩时刻"
                class="topic-input"
              />
            </div>
          </div>

          <!-- 标签 (仅在抖音可见) -->
          <div v-if="tab.selectedPlatform === 3" class="product-section">
            <h3>商品链接</h3>
            <el-input
              v-model="tab.productTitle"
              type="text"
              :rows="1"
              placeholder="请输入商品名称"
              maxlength="200"
              class="product-name-input"
            />
            <el-input
              v-model="tab.productLink"
              type="text"
              :rows="1"
              placeholder="请输入商品链接"
              maxlength="200"
              class="product-link-input"
            />
          </div>

          <!-- 定时发布 -->
          <div class="schedule-section">
            <h3>定时发布</h3>
            <div class="schedule-controls">
              <el-switch
                v-model="tab.scheduleEnabled"
                active-text="定时发布"
                inactive-text="立即发布"
              />
              <div v-if="tab.scheduleEnabled" class="schedule-settings">
                <div class="schedule-item">
                  <span class="label">每天发布视频数：</span>
                  <el-select v-model="tab.videosPerDay" placeholder="选择发布数量">
                    <el-option
                      v-for="num in 55"
                      :key="num"
                      :label="num"
                      :value="num"
                    />
                  </el-select>
                </div>
                <div class="schedule-item">
                  <span class="label">每天发布时间：</span>
                  <el-time-select
                    v-for="(time, index) in tab.dailyTimes"
                    :key="index"
                    v-model="tab.dailyTimes[index]"
                    start="00:00"
                    step="00:30"
                    end="23:30"
                    placeholder="选择时间"
                  />
                  <el-button
                    v-if="tab.dailyTimes.length < tab.videosPerDay"
                    type="primary"
                    size="small"
                    @click="tab.dailyTimes.push('10:00')"
                  >
                    添加时间
                  </el-button>
                </div>
                <div class="schedule-item">
                  <span class="label">开始天数：</span>
                  <el-select v-model="tab.startDays" placeholder="选择开始天数">
                    <el-option :label="'明天'" :value="0" />
                    <el-option :label="'后天'" :value="1" />
                  </el-select>
                </div>
              </div>
            </div>
          </div>

          <!-- AI作品标记 -->
          <div class="ai-content-section">
            <h3>AI内容声明</h3>
            <div class="ai-content-controls">
              <el-switch
                v-model="tab.isAiContent"
                active-text="这是AI生成的内容"
                inactive-text="非AI生成内容"
              />
              <div class="ai-content-hint">
                <el-icon><InfoFilled /></el-icon>
                <span>如果视频内容由AI生成，请开启此开关。部分平台要求标注AI内容。</span>
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="action-buttons">
            <el-button size="small" @click="cancelPublish(tab)">取消</el-button>
            <el-button size="small" type="primary" @click="confirmPublish(tab)">发布</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Upload, Plus, Close, Folder, Check, InfoFilled, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAccountStore } from '@/stores/account'
import { useAppStore } from '@/stores/app'
import { materialApi } from '@/api/material'
import { aiApi } from '@/api/ai'
import { dayjs } from 'element-plus'

// API base URL
const apiBaseUrl = import.meta.env.PROD ? '/api' : (import.meta.env.VITE_API_BASE_URL || '/api')

// Authorization headers
const authHeaders = computed(() => ({
  'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
}))

// 当前激活的tab
const activeTab = ref('tab1')

// tab计数器
let tabCounter = 1

// 获取应用状态管理
const appStore = useAppStore()

// 上传相关状态
const currentUploadTab = ref(null)
const materials = computed(() => appStore.materials)
const loadingMaterials = ref(false)
const currentPage = ref(1)

// 获取并展示素材
const fetchMaterials = async () => {
  loadingMaterials.value = true
  try {
    const response = await materialApi.getAllMaterials()
    if (response.code === 200) {
      // 假设后端返回的数据已经是按时间排序的，如果不是，前端排序
      const sorted = (response.data || []).sort((a, b) => {
        return new Date(b.upload_time).getTime() - new Date(a.upload_time).getTime()
      })
      appStore.setMaterials(sorted)
    }
  } catch (error) {
    console.error('获取素材列表失败:', error)
    ElMessage.error('获取素材列表失败')
  } finally {
    loadingMaterials.value = false
  }
}

// 分页显示素材
const displayedMaterials = computed(() => {
  const start = (currentPage.value - 1) * 5
  return materials.value.slice(start, start + 5)
})

const handlePageChange = (page) => {
  currentPage.value = page
}

const formatTime = (time) => {
  return dayjs ? dayjs(time).format('MM-DD HH:mm') : time
}

// 处理素材勾选变化
const handleMaterialSelectionChange = (selectedIds, tab) => {
  // 清空现有文件列表，重新根据选中ID生成
  tab.fileList = []
  
  selectedIds.forEach(id => {
    const material = materials.value.find(m => m.id === id)
    if (material) {
      const fileInfo = {
        name: material.filename,
        url: materialApi.getMaterialPreviewUrl(material.file_path.split('/').pop()),
        path: material.file_path,
        size: material.filesize * 1024 * 1024,
        type: 'video/mp4'
      }
      tab.fileList.push(fileInfo)
    }
  })
  
  // 更新显示列表
  tab.displayFileList = [...tab.fileList.map(item => ({
    name: item.name,
    url: item.url
  }))]
}

// 取消选中素材
const deselectMaterial = (tab, filePath) => {
  const material = materials.value.find(m => m.file_path === filePath)
  if (material) {
    const index = tab.selectedMaterialIds.indexOf(material.id)
    if (index > -1) {
      tab.selectedMaterialIds.splice(index, 1)
      handleMaterialSelectionChange(tab.selectedMaterialIds, tab)
    }
  }
}

// 批量发布相关状态
const batchPublishing = ref(false)
const batchPublishMessage = ref('')
const batchPublishType = ref('info')

// 平台列表 - 对应后端type字段
const platforms = [
  { key: 3, name: '抖音' },
  { key: 4, name: '快手' },
  { key: 2, name: '视频号' },
  { key: 1, name: '小红书' },
  { key: 5, name: 'TikTok' }
]

const platformNameMap = platforms.reduce((acc, platform) => {
  acc[platform.key] = platform.name
  return acc
}, {})

const defaultTabInit = {
  name: 'tab1',
  label: '发布1',
  fileList: [], // 后端返回的文件名列表
  displayFileList: [], // 用于显示的文件列表
  selectedAccounts: [], // 选中的账号ID列表
  selectedPlatform: 3, // 选中的平台（默认抖音）
  title: '',
  xhsTitle: '',
  productLink: '', // 商品链接
  productTitle: '', // 商品名称
  selectedTopics: [], // 话题列表（已废弃，保留用于兼容）
  topicInputValue: '', // 话题输入框内容
  scheduleEnabled: false, // 定时发布开关
  videosPerDay: 1, // 每天发布视频数量
  dailyTimes: ['10:00'], // 每天发布时间点列表
  startDays: 0, // 从今天开始计算的发布天数，0表示明天，1表示后天
  isAiContent: false, // 是否为AI生成内容
  publishStatus: null, // 发布状态，包含message和type
  aiTitleLoading: false,
  aiTopicLoading: false,
  aiXhsTitleLoading: false,
  selectedMaterialIds: [] // 选中的素材ID
}

// helper to create a fresh deep-copied tab from defaultTabInit
const makeNewTab = () => {
  // prefer structuredClone when available (newer browsers/node), fallback to JSON
  try {
    return typeof structuredClone === 'function' ? structuredClone(defaultTabInit) : JSON.parse(JSON.stringify(defaultTabInit))
  } catch (e) {
    return JSON.parse(JSON.stringify(defaultTabInit))
  }
}

// copy basic publish content from an existing tab (videos/title/topics)
const copyTabContent = (sourceTab, targetTab) => {
  if (!sourceTab || !targetTab) return
  targetTab.fileList = sourceTab.fileList.map(file => ({ ...file }))
  targetTab.displayFileList = sourceTab.displayFileList.map(file => ({ ...file }))
  targetTab.title = sourceTab.title
  targetTab.xhsTitle = sourceTab.xhsTitle
  targetTab.topicInputValue = sourceTab.topicInputValue
  targetTab.selectedTopics = [...sourceTab.selectedTopics]
  targetTab.selectedMaterialIds = [...sourceTab.selectedMaterialIds]
}

// tab页数据 - 默认只有一个tab (use deep copy to avoid shared refs)
const tabs = reactive([
  makeNewTab()
])

// 账号相关状态
const accountDialogVisible = ref(false)
const tempSelectedAccounts = ref([])
const currentTab = ref(null)

// 获取账号状态管理
const accountStore = useAccountStore()

// 根据选择的平台获取可用账号列表
const availableAccounts = computed(() => {
  const platformMap = {
    3: '抖音',
    2: '视频号',
    1: '小红书',
    4: '快手',
    5: 'TikTok'
  }
  const currentPlatform = currentTab.value ? platformMap[currentTab.value.selectedPlatform] : null
  return currentPlatform ? accountStore.accounts.filter(acc => acc.platform === currentPlatform) : []
})



const aiTargetLoadingMap = {
  title: 'aiTitleLoading',
  topics: 'aiTopicLoading',
  xhs_title: 'aiXhsTitleLoading'
}

const normalizeString = (value) => typeof value === 'string' ? value.trim() : ''

const buildAiContext = (tab) => {
  const safeTab = tab || {}
  const files = Array.isArray(safeTab.fileList) ? safeTab.fileList : []
  const fileNames = files
    .map(file => file?.name || file?.filename || (file?.path ? file.path.split('/').pop() : ''))
    .filter(Boolean)

  return {
    platformId: safeTab.selectedPlatform,
    platformName: platformNameMap[safeTab.selectedPlatform] || '',
    productTitle: normalizeString(safeTab.productTitle),
    productLink: normalizeString(safeTab.productLink),
    existingTitle: normalizeString(safeTab.title),
    existingXhsTitle: normalizeString(safeTab.xhsTitle),
    existingTopics: safeTab.topicInputValue 
      ? safeTab.topicInputValue.split(/[\s,，\n]+/).map(t => t.trim().replace(/^#/, '')).filter(Boolean)
      : [],
    fileNames
  }
}

const hasAiContext = (context) => {
  if (!context) return false
  if (context.existingTitle) return true
  if (context.existingXhsTitle) return true
  if (context.productTitle) return true
  if (context.productLink) return true
  if (Array.isArray(context.existingTopics) && context.existingTopics.length > 0) return true
  if (Array.isArray(context.fileNames) && context.fileNames.length > 0) return true
  return false
}

const triggerAiGeneration = async (tab, targets) => {
  if (!tab) {
    ElMessage.warning('请先选择一个发布Tab')
    return
  }

  const allowedTargets = ['title', 'topics', 'xhs_title']
  const normalizedTargets = (targets || []).filter(target => allowedTargets.includes(target))
  if (normalizedTargets.length === 0) {
    return
  }

  if (normalizedTargets.includes('xhs_title') && tab.selectedPlatform !== 1) {
    ElMessage.warning('小红书专用标题仅在选择小红书平台时可用')
    return
  }

  const context = buildAiContext(tab)
  if (!hasAiContext(context)) {
    ElMessage.warning('请先填写标题草稿、商品信息或上传素材，以便AI生成内容')
    return
  }

  const loadingKeys = normalizedTargets
    .map(target => aiTargetLoadingMap[target])
    .filter(Boolean)

  loadingKeys.forEach(key => {
    tab[key] = true
  })

  try {
    const response = await aiApi.generate({
      targets: normalizedTargets,
      context
    })

    const generated = response.data || {}
    let updated = false

    if (normalizedTargets.includes('title') && generated.title) {
      tab.title = generated.title
      updated = true
    }

    if (normalizedTargets.includes('topics') && Array.isArray(generated.topics)) {
      tab.topicInputValue = generated.topics.map(t => t.startsWith('#') ? t : `#${t}`).join(' ')
      // 兼容旧字段
      tab.selectedTopics = [...generated.topics]
      updated = true
    }

    if (normalizedTargets.includes('xhs_title') && generated.xhsTitle) {
      tab.xhsTitle = generated.xhsTitle
      if (tab.selectedPlatform === 1) {
        tab.title = generated.xhsTitle
      }
      updated = true
    }

    if (updated) {
      ElMessage.success('AI生成完成')
    } else {
      ElMessage.warning('AI未返回有效内容')
    }
  } catch (error) {
    console.error('AI生成失败:', error)
    ElMessage.error(error?.message || 'AI生成失败，请稍后重试')
  } finally {
    loadingKeys.forEach(key => {
      tab[key] = false
    })
  }
}

const requestAiTitle = (tab) => triggerAiGeneration(tab, ['title'])
const requestAiTopics = (tab) => triggerAiGeneration(tab, ['topics'])
const requestAiXhsTitle = (tab) => triggerAiGeneration(tab, ['xhs_title'])

// 添加新tab
const addTab = () => {
  tabCounter++
  const newTab = makeNewTab()
  const tab1 = tabs.find(tab => tab.name === 'tab1') || tabs[0]
  if (tab1) {
    copyTabContent(tab1, newTab)
    newTab.selectedPlatform = null
  }
  newTab.name = `tab${tabCounter}`
  newTab.label = `发布${tabCounter}`
  tabs.push(newTab)
  activeTab.value = newTab.name
}

// 删除tab
const removeTab = (tabName) => {
  const index = tabs.findIndex(tab => tab.name === tabName)
  if (index > -1) {
    tabs.splice(index, 1)
    // 如果删除的是当前激活的tab，切换到第一个tab
    if (activeTab.value === tabName && tabs.length > 0) {
      activeTab.value = tabs[0].name
    }
  }
}

// 处理文件上传成功
const handleUploadSuccess = (response, file, tab) => {
  if (response.code === 200) {
    // 刷新素材库
    fetchMaterials().then(() => {
      // 自动选中新上传的素材
      // 假设最新上传的在第一个
      if (materials.value.length > 0) {
        const newMaterial = materials.value[0]
        if (!tab.selectedMaterialIds.includes(newMaterial.id)) {
          tab.selectedMaterialIds.push(newMaterial.id)
          handleMaterialSelectionChange(tab.selectedMaterialIds, tab)
        }
      }
    })
    
    ElMessage.success('文件上传成功')
  } else {
    ElMessage.error(response.msg || '上传失败')
  }
}

// 处理文件上传失败
const handleUploadError = (error) => {
  ElMessage.error('文件上传失败')
  console.error('上传错误:', error)
}

// 删除已上传文件 (已废弃，改用 deselectMaterial)
const removeFile = (tab, index) => {
  // 从文件列表中删除
  tab.fileList.splice(index, 1)
  
  // 更新显示列表
  tab.displayFileList = [...tab.fileList.map(item => ({
    name: item.name,
    url: item.url
  }))]
  
  ElMessage.success('文件删除成功')
}

// 账号选择相关方法
// 打开账号选择弹窗
const openAccountDialog = (tab) => {
  currentTab.value = tab
  tempSelectedAccounts.value = [...tab.selectedAccounts]
  accountDialogVisible.value = true
}

// 确认账号选择
const confirmAccountSelection = () => {
  if (currentTab.value) {
    currentTab.value.selectedAccounts = [...tempSelectedAccounts.value]
  }
  accountDialogVisible.value = false
  currentTab.value = null
  ElMessage.success('账号选择完成')
}

// 删除选中的账号
const removeAccount = (tab, index) => {
  tab.selectedAccounts.splice(index, 1)
}

// 获取账号显示名称
const getAccountDisplayName = (accountId) => {
  const account = accountStore.accounts.find(acc => acc.id === accountId)
  return account ? account.name : accountId
}

// 取消发布
const cancelPublish = (tab) => {
  ElMessage.info('已取消发布')
}

// 确认发布
const confirmPublish = async (tab) => {
  return new Promise((resolve, reject) => {
    // 数据验证
    if (tab.fileList.length === 0) {
      ElMessage.error('请先上传视频文件')
      reject(new Error('请先上传视频文件'))
      return
    }
    if (!tab.selectedPlatform) {
      ElMessage.error('请选择发布平台')
      reject(new Error('请选择发布平台'))
      return
    }
    if (tab.selectedAccounts.length === 0) {
      ElMessage.error('请选择发布账号')
      reject(new Error('请选择发布账号'))
      return
    }
    
    const baseTitle = tab.title ? tab.title.trim() : ''
    const xhsTitleValue = tab.xhsTitle ? tab.xhsTitle.trim() : ''
    const resolvedTitle = tab.selectedPlatform === 1
      ? (xhsTitleValue || baseTitle)
      : baseTitle

    if (!resolvedTitle) {
      ElMessage.error('请输入标题')
      reject(new Error('请输入标题'))
      return
    }

    if (tab.selectedPlatform === 1 && resolvedTitle.length > 20) {
      ElMessage.error('小红书标题不能超过20个字符')
      reject(new Error('小红书标题不能超过20个字符'))
      return
    }

    // 解析话题
    const tags = tab.topicInputValue
      ? tab.topicInputValue.split(/[\s,，\n]+/).map(t => t.trim().replace(/^#/, '')).filter(Boolean)
      : []

    // 构造发布数据，符合后端API格式
    const publishData = {
      type: tab.selectedPlatform,
      title: resolvedTitle,
      xhsTitle: xhsTitleValue,
      tags: tags, // 不带#号的话题列表
      fileList: tab.fileList.map(file => file.path), // 只发送文件路径
      accountList: tab.selectedAccounts.map(accountId => {
        const account = accountStore.accounts.find(acc => acc.id === accountId)
        return account ? account.filePath : accountId
      }), // 发送账号的文件路径
      enableTimer: tab.scheduleEnabled ? 1 : 0, // 是否启用定时发布，开启传1，不开启传0
      videosPerDay: tab.scheduleEnabled ? tab.videosPerDay || 1 : 1, // 每天发布视频数量，1-55
      dailyTimes: tab.scheduleEnabled ? tab.dailyTimes || ['10:00'] : ['10:00'], // 每天发布时间点
      startDays: tab.scheduleEnabled ? tab.startDays || 0 : 0, // 从今天开始计算的发布天数，0表示明天，1表示后天
      category: 0, //表示非原创
      productLink: tab.productLink.trim() || '', // 商品链接
      productTitle: tab.productTitle.trim() || '', // 商品名称
      isAiContent: tab.isAiContent ? 1 : 0 // 是否为AI生成内容，开启传1，不开启传0
    }
    
    // 调用后端发布API
    fetch(`${apiBaseUrl}/postVideo`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders.value
      },
      body: JSON.stringify(publishData)
    })
    .then(response => response.json())
    .then(data => {
      if (data.code === 200) {
        tab.publishStatus = {
          message: '发布成功',
          type: 'success'
        }
        // 清空当前tab的数据
        tab.fileList = []
        tab.displayFileList = []
        tab.title = ''
        tab.xhsTitle = ''
        tab.topicInputValue = ''
        tab.selectedTopics = []
        tab.selectedAccounts = []
        tab.scheduleEnabled = false
        tab.isAiContent = false
        tab.aiTitleLoading = false
        tab.aiTopicLoading = false
        tab.aiXhsTitleLoading = false
        resolve()
      } else {
        tab.publishStatus = {
          message: `发布失败：${data.msg || '发布失败'}`,
          type: 'error'
        }
        reject(new Error(data.msg || '发布失败'))
      }
    })
    .catch(error => {
      console.error('发布错误:', error)
      tab.publishStatus = {
        message: '发布失败，请检查网络连接',
        type: 'error'
      }
      reject(error)
    })
  })
}

// 显示上传选项
const showUploadOptions = (tab) => {
  currentUploadTab.value = tab
  uploadOptionsVisible.value = true
}

// 选择本地上传
const selectLocalUpload = () => {
  uploadOptionsVisible.value = false
  localUploadVisible.value = true
}

// 选择素材库
const selectMaterialLibrary = async () => {
  uploadOptionsVisible.value = false
  
  // 如果素材库为空，先获取素材数据
  if (materials.value.length === 0) {
    try {
      const response = await materialApi.getAllMaterials()
      if (response.code === 200) {
        appStore.setMaterials(response.data)
      } else {
        ElMessage.error('获取素材列表失败')
        return
      }
    } catch (error) {
      console.error('获取素材列表出错:', error)
      ElMessage.error('获取素材列表失败')
      return
    }
  }
  
  selectedMaterials.value = []
  materialLibraryVisible.value = true
}

// 确认素材选择
const confirmMaterialSelection = () => {
  if (selectedMaterials.value.length === 0) {
    ElMessage.warning('请选择至少一个素材')
    return
  }
  
  if (currentUploadTab.value) {
    // 将选中的素材添加到当前tab的文件列表
    selectedMaterials.value.forEach(materialId => {
      const material = materials.value.find(m => m.id === materialId)
      if (material) {
        const fileInfo = {
          name: material.filename,
          url: materialApi.getMaterialPreviewUrl(material.file_path.split('/').pop()),
          path: material.file_path,
          size: material.filesize * 1024 * 1024, // 转换为字节
          type: 'video/mp4'
        }
        
        // 检查是否已存在相同文件
        const exists = currentUploadTab.value.fileList.some(file => file.path === fileInfo.path)
        if (!exists) {
          currentUploadTab.value.fileList.push(fileInfo)
        }
      }
    })
    
    // 更新显示列表
    currentUploadTab.value.displayFileList = [...currentUploadTab.value.fileList.map(item => ({
      name: item.name,
      url: item.url
    }))]
  }
  
  const addedCount = selectedMaterials.value.length
  materialLibraryVisible.value = false
  selectedMaterials.value = []
  currentUploadTab.value = null
  ElMessage.success(`已添加 ${addedCount} 个素材`)
}

// 批量发布对话框状态
const batchPublishDialogVisible = ref(false)
const currentPublishingTab = ref(null)
const publishProgress = ref(0)
const publishResults = ref([])
const isCancelled = ref(false)

// 取消批量发布
const cancelBatchPublish = () => {
  isCancelled.value = true
  ElMessage.info('正在取消发布...')
}

// 批量发布方法
const batchPublish = async () => {
  if (batchPublishing.value) return
  
  batchPublishing.value = true
  currentPublishingTab.value = null
  publishProgress.value = 0
  publishResults.value = []
  isCancelled.value = false
  batchPublishDialogVisible.value = true
  
  try {
    for (let i = 0; i < tabs.length; i++) {
      if (isCancelled.value) {
        publishResults.value.push({
          label: tabs[i].label,
          status: 'cancelled',
          message: '已取消'
        })
        continue
      }

      const tab = tabs[i]
      currentPublishingTab.value = tab
      publishProgress.value = Math.floor((i / tabs.length) * 100)
      
      try {
        await confirmPublish(tab)
        publishResults.value.push({
          label: tab.label,
          status: 'success',
          message: '发布成功'
        })
      } catch (error) {
        publishResults.value.push({
          label: tab.label,
          status: 'error',
          message: error.message
        })
        // 不立即返回，继续显示发布结果
      }
    }
    
    publishProgress.value = 100
    
    // 统计发布结果
    const successCount = publishResults.value.filter(r => r.status === 'success').length
    const failCount = publishResults.value.filter(r => r.status === 'error').length
    const cancelCount = publishResults.value.filter(r => r.status === 'cancelled').length
    
    if (isCancelled.value) {
      ElMessage.warning(`发布已取消：${successCount}个成功，${failCount}个失败，${cancelCount}个未执行`)
    } else if (failCount > 0) {
      ElMessage.error(`发布完成：${successCount}个成功，${failCount}个失败`)
    } else {
      ElMessage.success('所有Tab发布成功')
      setTimeout(() => {
        batchPublishDialogVisible.value = false
      }, 1000)
    }
    
  } catch (error) {
    console.error('批量发布出错:', error)
    ElMessage.error('批量发布出错，请重试')
  } finally {
    batchPublishing.value = false
    isCancelled.value = false
  }
}
onMounted(() => {
  fetchMaterials()
})
</script>

<style lang="scss" scoped>
@use '@/styles/variables.scss' as *;

.publish-center {
  display: flex;
  flex-direction: column;
  height: 100%;
  
  // Tab管理区域
  .tab-management {
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
    padding: 15px 20px;
    
    .tab-header {
      display: flex;
      align-items: flex-start;
      gap: 15px;
      
      .tab-list {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        flex: 1;
        min-width: 0;
        
        .tab-item {
           display: flex;
           align-items: center;
           gap: 6px;
           padding: 6px 12px;
           background-color: #f5f7fa;
           border: 1px solid #dcdfe6;
           border-radius: 4px;
           cursor: pointer;
           transition: all 0.3s;
           font-size: 14px;
           height: 32px;
           
           &:hover {
             background-color: #ecf5ff;
             border-color: #b3d8ff;
           }
           
           &.active {
             background-color: #409eff;
             border-color: #409eff;
             color: #fff;
             
             .close-icon {
               color: #fff;
               
               &:hover {
                 background-color: rgba(255, 255, 255, 0.2);
               }
             }
           }
           
           .close-icon {
             padding: 2px;
             border-radius: 2px;
             cursor: pointer;
             transition: background-color 0.3s;
             font-size: 12px;
             
             &:hover {
               background-color: rgba(0, 0, 0, 0.1);
             }
           }
         }
       }
       
      .tab-actions {
        display: flex;
        gap: 10px;
        flex-shrink: 0;
        
        .add-tab-btn,
        .batch-publish-btn {
          display: flex;
          align-items: center;
          gap: 4px;
          height: 32px;
          padding: 6px 12px;
          font-size: 14px;
          white-space: nowrap;
        }
      }
    }
  }
  
  // 批量发布进度对话框样式
  .publish-progress {
    padding: 20px;
    
    .current-publishing {
      margin: 15px 0;
      text-align: center;
      color: #606266;
    }

    .publish-results {
      margin-top: 20px;
      border-top: 1px solid #EBEEF5;
      padding-top: 15px;
      max-height: 300px;
      overflow-y: auto;

      .result-item {
        display: flex;
        align-items: center;
        padding: 8px 0;
        color: #606266;

        .el-icon {
          margin-right: 8px;
        }

        .label {
          margin-right: 10px;
          font-weight: 500;
        }

        .message {
          color: #909399;
        }

        &.success {
          color: #67C23A;
        }

        &.error {
          color: #F56C6C;
        }

        &.cancelled {
          color: #909399;
        }
      }
    }
  }

  .dialog-footer {
    text-align: right;
  }
  
  // 内容区域
  .publish-content {
    flex: 1;
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    padding: 20px;
    
    .tab-content-wrapper {
      display: flex;
      justify-content: center;
      
      .tab-content {
        width: 100%;
        max-width: 800px;
        
        h3 {
          font-size: 16px;
          font-weight: 500;
          color: $text-primary;
          margin: 0 0 10px 0;
        }

        .section-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 10px;

          h3 {
            margin: 0;
          }

          .ai-generate-btn {
            flex-shrink: 0;
          }
        }
        
        .upload-section,
        .account-section,
        .platform-section,
        .title-section,
        .product-section,
        .topic-section,
        .schedule-section,
        .ai-content-section {
          margin-bottom: 30px;
        }

        .ai-content-section {
          .ai-content-controls {
            display: flex;
            flex-direction: column;
            gap: 12px;

            .ai-content-hint {
              display: flex;
              align-items: center;
              gap: 8px;
              padding: 12px;
              background-color: #f4f4f5;
              border-radius: 4px;
              font-size: 13px;
              color: #606266;

              .el-icon {
                flex-shrink: 0;
                font-size: 16px;
                color: #909399;
              }

              span {
                line-height: 1.5;
              }
            }
          }
        }

        .product-section {
          .product-name-input,
          .product-link-input {
            margin-bottom: 5px;
          }
        }
        
        .video-upload {
          width: 100%;
          
          :deep(.el-upload-dragger) {
            width: 100%;
            height: 180px;
          }
        }
        
        .account-input {
          max-width: 400px;
        }
        
        .platform-buttons {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          
          .platform-btn {
            min-width: 80px;
          }
        }
        
        .title-input {
          max-width: 600px;
        }

        .xhs-title-section {
          margin-top: 12px;
          padding: 12px;
          border: 1px solid #ebeef5;
          border-radius: 6px;
          background-color: #f8f9fb;

          .xhs-title-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 8px;

            span {
              font-size: 14px;
              font-weight: 500;
              color: #303133;
            }
          }

          .xhs-title-input {
            max-width: 450px;
          }

          .xhs-title-hint {
            margin: 6px 0 0 0;
            font-size: 12px;
            color: #909399;
          }
        }
        
        .topic-display {
          display: flex;
          flex-direction: column;
          gap: 12px;
          
          .topic-input {
            width: 100%;
          }
        }
        
        .schedule-controls {
          display: flex;
          flex-direction: column;
          gap: 15px;

          .schedule-settings {
            margin-top: 15px;
            padding: 15px;
            background-color: #f5f7fa;
            border-radius: 4px;

            .schedule-item {
              display: flex;
              align-items: center;
              margin-bottom: 15px;

              &:last-child {
                margin-bottom: 0;
              }

              .label {
                min-width: 120px;
                margin-right: 10px;
              }

              .el-time-select {
                margin-right: 10px;
              }

              .el-button {
                margin-left: 10px;
              }
            }
          }
        }
        
        .action-buttons {
          display: flex;
          justify-content: flex-end;
          gap: 10px;
          margin-top: 30px;
          padding-top: 20px;
          border-top: 1px solid #ebeef5;
        }
      }
    }
  }
  
  // 已上传文件列表样式
  .selected-files-preview {
    margin-top: 20px;
    
    h4 {
      font-size: 14px;
      font-weight: 500;
      margin-bottom: 12px;
      color: #606266;
    }
    
    .file-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      
      .file-item {
        display: flex;
        align-items: center;
        padding: 8px 12px;
        background-color: #f5f7fa;
        border-radius: 4px;
        
        .el-link {
          margin-right: 10px;
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          justify-content: flex-start;
        }
        
        .remove-btn {
          padding: 2px;
          height: auto;
          color: #909399;
          
          &:hover {
            color: #f56c6c;
          }
        }
      }
    }
  }

  // 素材选择区域样式
  .material-selection-area {
    margin-top: 15px;
    min-height: 100px;
    
    .loading-placeholder,
    .empty-placeholder {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100px;
      color: #909399;
      font-size: 14px;
      background-color: #f9fafe;
      border-radius: 4px;
      gap: 8px;
    }

    .material-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 10px;
    }

    .material-card {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 15px;
      border: 1px solid #dcdfe6;
      border-radius: 4px;
      transition: all 0.3s;
      background-color: #fff;

      &:hover {
        border-color: #409eff;
        background-color: #f0f9eb;
      }

      &.is-selected {
        border-color: #67c23a;
        background-color: #f0f9eb;
      }

      .material-checkbox {
        display: flex;
        align-items: center;
        flex: 1;
        margin-right: 15px;
        overflow: hidden;
        
        :deep(.el-checkbox__label) {
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .material-name {
          font-size: 14px;
          color: #303133;
        }
      }

      .material-meta {
        display: flex;
        align-items: center;
        gap: 15px;
        font-size: 12px;
        color: #909399;
        flex-shrink: 0;

        .file-size {
          min-width: 60px;
          text-align: right;
        }

        .upload-time {
          min-width: 90px;
          text-align: right;
        }
      }
    }

    .pagination-wrapper {
      margin-top: 15px;
      display: flex;
      justify-content: flex-end;
    }
  }
  
  // 添加话题弹窗样式 - 已废弃
}
</style>

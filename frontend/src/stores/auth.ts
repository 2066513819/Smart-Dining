﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE_URL =
  (import.meta as any)?.env?.VITE_API_BASE_URL ||
  (typeof window !== 'undefined' && window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : `${window.location.protocol}//${window.location.hostname}:8000`)

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
  },
  timeout: 60000,
  paramsSerializer: (params) => {
    const searchParams = new URLSearchParams()
    for (const key in params) {
      const value = params[key]
      if (value === undefined || value === null || value === '') continue
      if (Array.isArray(value)) {
        value.forEach(v => {
          if (v !== undefined && v !== null && v !== '') {
            searchParams.append(key, v)
          }
        })
      } else {
        searchParams.append(key, value)
      }
    }
    return searchParams.toString()
  }
})

// 请求拦截器，添加token和防缓存机制
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    console.log(`请求拦截器 - URL: ${config.url}`)
    console.log(`请求拦截器 - 从localStorage获取到的token: ${token}`)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      console.log(`请求拦截器 - 添加到请求头的Authorization: ${config.headers.Authorization}`)
    } else {
      console.log(`请求拦截器 - 未找到token，未添加Authorization头`)
    }
    
    // 只对GET请求添加时间戳，防止缓存
    if (config.method === 'get') {
      if (!config.params) {
        config.params = {}
      }
      config.params._t = Date.now()
    }
    
    return config
  },
  error => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器，处理401错误和其他错误
api.interceptors.response.use(
  response => {
    console.log(`响应拦截器 - URL: ${response.config.url}`)
    console.log(`响应拦截器 - 状态码: ${response.status}`)
    console.log(`响应拦截器 - 响应数据: ${JSON.stringify(response.data, null, 2)}`)
    // 成功响应直接返回响应数据，方便前端使用
    return response.data
  },
  error => {
    // 详细打印错误信息，便于调试
    console.error('响应拦截器错误:', error)
    console.error('错误名称:', error.name)
    console.error('错误代码:', error.code)
    console.error('错误配置:', error.config)
    console.error('错误请求:', error.request)
    console.error('错误响应:', error.response)
    
    // 处理401未授权错误
    if (error.response?.status === 401) {
      console.error('401错误，清除token并跳转到登录页')
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    
    return Promise.reject(error)
  }
)

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as any,
    token: localStorage.getItem('token') || '',
    isLoggedIn: false,
    initialized: false
  }),
  
  actions: {
    // 初始化认证状态，验证token有效性
    async initAuth() {
      if (this.initialized) return
      
      const token = localStorage.getItem('token')
      if (token) {
        try {
          // 尝试获取用户信息，验证token是否有效
          await this.fetchUser()
          this.token = token
          this.isLoggedIn = true
        } catch (error) {
          // token无效，清除token
          console.error('Token验证失败，清除token:', error)
          this.logout()
        }
      } else {
        this.isLoggedIn = false
      }
      this.initialized = true
    },
    
    async adminListUsers() {
      try {
        // 响应拦截器返回 response.data，与 Axios 默认类型不一致
        const res = (await api.get('/auth/users', {
          params: { page_size: 100 }
        })) as { items?: any[] }
        return res.items || []
      } catch (error) {
        console.error('Failed to list users:', error)
        throw error
      }
    },
    
    async adminUpdateUserRole(userId: number, role: 'admin' | 'user') {
      try {
        const data = await api.put(`/auth/users/${userId}`, { role })
        return data
      } catch (error) {
        console.error('Failed to update user role:', error)
        throw error
      }
    },
    
    async login(username: string, password: string) {
      try {
        // 登录前清除推荐结果缓存
        const recStore = useRecommendationStore()
        recStore.smartRecommendations = []
        recStore.databaseRecommendations = []
        recStore.recommendations = null
        recStore.analysisResults = null
        
        // 响应拦截器已处理，直接返回data
        const data = await api.post('/auth/token', {
          username,
          password
        }, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          },
          transformRequest: [(data) => {
            return Object.entries(data).map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`).join('&')
          }]
        }) as any
        
        // 直接使用返回的数据
        this.token = data.access_token
        this.isLoggedIn = true
        localStorage.setItem('token', this.token)
        
        // 获取用户信息
        await this.fetchUser()
        
        return data
      } catch (error) {
        console.error('Login failed:', error)
        throw error
      }
    },
    
    async register(userData: any) {
      try {
        // 响应拦截器已处理，直接返回data
        const data = await api.post('/auth/register', userData)
        return data
      } catch (error) {
        console.error('Registration failed:', error)
        throw error
      }
    },
    
    async fetchUser() {
      try {
        // 响应拦截器已处理，直接返回data
        const userData = await api.get('/auth/me')
        this.user = userData
        return userData
      } catch (error) {
        console.error('Failed to fetch user:', error)
        this.logout()
        throw error
      }
    },
    
    async uploadAvatar(file: File) {
      try {
        const formData = new FormData()
        formData.append('file', file)
        
        // 响应拦截器已处理，直接返回data
        const userData = await api.post('/auth/avatar', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        // 更新用户信息
        this.user = userData
        return userData
      } catch (error) {
        console.error('Failed to upload avatar:', error)
        throw error
      }
    },
    
    async updateProfile(profileData: any) {
      try {
        // 响应拦截器已处理，直接返回data
        const userData = await api.put('/auth/profile', profileData)
        this.user = userData
        return userData
      } catch (error) {
        console.error('Failed to update profile:', error)
        throw error
      }
    },
    
    logout() {
      this.user = null
      this.token = ''
      this.isLoggedIn = false
      localStorage.removeItem('token')
      // 清除推荐结果缓存
      const recStore = useRecommendationStore()
      recStore.smartRecommendations = []
      recStore.databaseRecommendations = []
      recStore.recommendations = null
      recStore.analysisResults = null
    }
  }
})

export const useRecommendationStore = defineStore('recommendation', {
  state: () => ({
    recommendations: null as any | null,
    databaseRecommendations: [] as any[],
    smartRecommendations: [] as any[], // 智能推荐结果缓存
    analysisResults: null as any | null,
    loading: false,
    error: null as string | null,
    api: api // 暴露 api 实例供外部使用
  }),
  
  actions: {
    async getRecommendation(mealType: string, cycle: string, ageGroup: string, userId: string) {
      this.loading = true
      this.error = null
      try {
        const data = await api.post('/recommendation/get-recommendation', {
          meal_type: mealType,
          cycle: cycle,
          age_group: ageGroup,
          user_id: userId
        }, { timeout: 60000 })
        this.recommendations = data
        return data
      } catch (error: any) {
        this.error = error.message || 'Failed to get recommendation'
        throw error
      } finally {
        this.loading = false
      }
    },
    // 新增：使用完整 prompt 获取智能推荐（前端将规则拼接成 prompt）
    async getRecommendationByPrompt(prompt: string, userId: string) {
      this.loading = true
      this.error = null
      try {
        const data = await api.post('/recommendation/get-recommendation', {
          prompt: prompt,
          user_id: userId,
          meal_type: '各类',
          cycle: '1天',
          age_group: 'primary'
        }, { timeout: 60000 })
        this.recommendations = data
        return data
      } catch (error: any) {
        this.error = error.message || 'Failed to get recommendation by prompt'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async analyzeDishes(mealType: string, cycle: string, ageGroup: string, userId: string) {
      this.loading = true
      this.error = null
      try {
        const data = await api.post('/recommendation/analyze-dishes', {
          meal_type: mealType,
          cycle: cycle,
          age_group: ageGroup,
          user_id: userId
        }, { timeout: 60000 })
        // 菜品分析结果使用独立的存储，避免覆盖推荐结果
        this.analysisResults = data
        return data
      } catch (error: any) {
        this.error = error.message || 'Failed to analyze dishes'
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async saveDish(dishData: any) {
      try {
        // 响应拦截器已处理，直接返回data
        // 使用不带尾随斜杠的路径，避免重定向导致CORS问题
        const data = await api.post('/dish', dishData)
        console.log('Dish saved successfully:', data)
        return data
      } catch (error: any) {
        console.error('Failed to save dish:', error)
        console.error('Error details:', {
          name: error.name,
          code: error.code,
          message: error.message,
          response: error.response,
          request: error.request,
          config: error.config
        })
        throw error
      }
    },

    async publishMealPlan(payload: any) {
      try {
        const data = await api.post('/meal_plans/publish', payload)
        return data
      } catch (error: any) {
        console.error('Failed to publish meal plan:', error)
        throw error
      }
    },
    async getPublishedMealPlans() {
      try {
        const data = await api.get('/meal_plans/published')
        return data
      } catch (error) {
        console.error('Failed to get published meal plans:', error)
        throw error
      }
    },
    async getDishById(dishId: number) {
      try {
        const data = await api.get(`/dish/${dishId}`)
        return data
      } catch (error) {
        console.error(`Failed to get dish ${dishId}:`, error)
        throw error
      }
    },
    async getMenuItemById(itemId: number) {
      try {
        const data = await api.get(`/menu_items/${itemId}`)
        return data
      } catch (error) {
        console.error(`Failed to get menu item ${itemId}:`, error)
        throw error
      }
    },
    
    async getDishes(skip: number = 0, limit: number = 100) {
      try {
        // 响应拦截器已处理，直接返回data
        const data = await api.get('/dish', {
          params: {
            skip,
            limit
          }
        })
        return data
      } catch (error) {
        console.error('Failed to get dishes:', error)
        throw error
      }
    },
    
    async countDishes() {
      try {
        const data = await api.get('/dish/count')
        return data
      } catch (error) {
        console.error('Failed to count dishes:', error)
        throw error
      }
    },
    
    async deleteDish(dishId: number) {
      try {
        // 响应拦截器已处理，直接返回data
        const data = await api.delete(`/dish/${dishId}`)
        return data
      } catch (error) {
        console.error('Failed to delete dish:', error)
        throw error
      }
    },
    
    async updateDish(dishId: number, dishData: any) {
      try {
        // 响应拦截器已处理，直接返回data
        const data = await api.put(`/dish/${dishId}`, dishData)
        return data
      } catch (error) {
        console.error('Failed to update dish:', error)
        throw error
      }
    },
    
    // 管理员：获取所有菜品
    async adminListAllDishes() {
      try {
        try {
          const data = await api.get('/dish/admin')
          return data
        } catch (err: any) {
          if (err?.response?.status === 404) {
            const data = await api.get('/dish/admin/')
            return data
          }
          throw err
        }
      } catch (error) {
        console.error('Failed to list all dishes:', error)
        throw error
      }
    },
    // 管理员：更新菜品发布状态
    async adminUpdateDishPublish(dishId: number, is_published: number) {
      try {
        try {
          const data = await api.put(`/dish/admin/${dishId}/publish`, { is_published })
          return data
        } catch (err: any) {
          if (err?.response?.status === 404) {
            const data = await api.put(`/dish/admin/${dishId}/publish/`, { is_published })
            return data
          }
          throw err
        }
      } catch (error) {
        console.error('Failed to update dish publish:', error)
        throw error
      }
    },
    async adminGetDishStats(days: number = 14) {
      try {
        const data = await api.get('/menu_items/admin/stats', { params: { days } })
        return data
      } catch (error) {
        console.error('Failed to get dish stats:', error)
        throw error
      }
    },
    
    // 获取数据库菜品推荐
    async getDatabaseRecommendation(params: any) {
      console.log('store.getDatabaseRecommendation开始执行，参数:', params)
      this.loading = true
      this.error = null
      try {
        const data = await api.post('/recommendation/database-recommendation', params, { timeout: 60000 })
        console.log('API返回数据:', data)
        
        // 检查data是否有效，避免设置无效数据
        if (data) {
          // 将推荐结果保存到databaseRecommendations，这样切换页面后推荐信息还能保留
          this.databaseRecommendations = Array.isArray(data) ? data : [data]
          this.recommendations = data
          console.log('更新后的databaseRecommendations:', this.databaseRecommendations)
        } else {
          console.warn('API返回了无效数据，不更新databaseRecommendations')
          // 确保databaseRecommendations始终是数组
          this.databaseRecommendations = []
        }
        return data
      } catch (error: any) {
        console.error('API调用失败:', error)
        this.error = error.message || 'Failed to get database recommendation'
        // 确保databaseRecommendations始终是数组
        this.databaseRecommendations = []
        throw error
      } finally {
        this.loading = false
        console.log('store.getDatabaseRecommendation执行完毕')
      }
    }
    ,
    async listAllDishes() {
      try {
        const data = await api.get('/dish/all')
        return data
      } catch (error) {
        console.error('Failed to list all dishes:', error)
        throw error
      }
    },
    async countAllDishes() {
      try {
        const data = await api.get('/dish/count-all')
        return data
      } catch (error) {
        console.error('Failed to count all dishes:', error)
        throw error
      }
    }

    ,
    async listMenuItems(skip: number = 0, limit: number = 100, filters: any = {}) {
      try {
        const params = { skip, limit, ...filters }
        const data = await api.get('/menu_items', { params })
        return data
      } catch (error) {
        console.error('Failed to list menu items:', error)
        throw error
      }
    },
    async countMenuItems(filters: any = {}) {
      try {
        const data = await api.get('/menu_items/count', { params: { ...filters } })
        return data
      } catch (error) {
        console.error('Failed to count menu items:', error)
        throw error
      }
    },
    async createMenuItem(item: any) {
      try {
        const data = await api.post('/menu_items', item)
        return data
      } catch (error) {
        console.error('Failed to create menu item:', error)
        throw error
      }
    },
    async updateMenuItem(id: number, item: any) {
      try {
        const data = await api.put(`/menu_items/${id}`, item)
        return data
      } catch (error) {
        console.error('Failed to update menu item:', error)
        throw error
      }
    },
    async deleteMenuItem(id: number) {
      try {
        const data = await api.delete(`/menu_items/${id}`)
        return data
      } catch (error) {
        console.error('Failed to delete menu item:', error)
        throw error
      }
    }

  }
})

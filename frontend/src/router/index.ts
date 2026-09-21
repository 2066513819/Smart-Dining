import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import RecommendationView from '../views/RecommendationView.vue'
import HomeView from '../views/HomeView.vue'
import ProfileView from '../views/ProfileView.vue'

import { useAuthStore } from '../stores/auth'
import Layout from '../components/Layout.vue' // 引入Layout组件

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView
    },
    {
      // 主布局路由
      path: '/',
      component: Layout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: 'home'
        },
        {
          path: 'home',
          name: 'home',
          component: HomeView,
          meta: { requiresAuth: true, title: '首页' }
        },
        {
          path: 'recommendation',
          name: 'recommendation',
          component: RecommendationView,
          meta: { requiresAuth: true, title: '菜谱制定' }
        },
        {
          path: 'meal-rules',
          name: 'meal-rules',
          component: () => import('../views/MealRulesView.vue'),
          meta: { requiresAuth: true, title: '餐饮设置' }
        },
        {
          path: 'history-plans',
          name: 'history-plans',
          component: () => import('../views/HistoryPlansView.vue'),
          meta: { requiresAuth: true, title: '历史菜谱' }
        },
        {
          path: 'profile',
          name: 'profile',
          component: ProfileView,
          meta: { requiresAuth: true, title: '个人中心' }
        },


        {
          // 账户设置
          path: 'settings',
          name: 'settings',
          component: () => import('../views/SettingsView.vue'),
          meta: { requiresAuth: true, title: '账户设置' }
        },
        {
          // 修改密码
          path: 'change-password',
          name: 'change-password',
          component: () => import('../views/ChangePasswordView.vue'),
          meta: { requiresAuth: true, title: '修改密码' }
        },

        {
          // 菜品列表（原菜品管理）
          path: 'dish-management',
          name: 'dish-management',
          component: () => import('../views/DishManagementView.vue'),
          meta: { requiresAuth: true, title: '菜品列表' }
        },
        {
          // 食材成本
          path: 'ingredient-cost',
          name: 'ingredient-cost',
          component: () => import('../views/IngredientCostView.vue'),
          meta: { requiresAuth: true, title: '食材成本' }
        },
        {
          // 食材营养统计
          path: 'ingredient-nutrition',
          name: 'ingredient-nutrition',
          component: () => import('../views/IngredientNutritionView.vue'),
          meta: { requiresAuth: true, title: '食材营养统计' }
        },
        {
          // 添加菜品
          path: 'add-dish',
          name: 'add-dish',
          component: () => import('../views/AddDishView.vue'),
          meta: { requiresAuth: true, title: '添加菜品' }
        },
        {
          // 菜谱制作方法
          path: 'recipe-method',
          name: 'recipe-method',
          component: () => import('../views/RecipeMethodView.vue'),
          meta: { requiresAuth: true, title: '制作方法' }
        },
        {
          // 管理员面板
          path: 'admin',
          name: 'admin',
          component: () => import('../views/AdminDashboard.vue'),
          meta: { requiresAuth: true, requiresAdmin: true, title: '管理员面板' }
        }
      ]
    }
  ]
})

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  console.log('Navigating to:', to.path)
  const authStore = useAuthStore()
  
  // 初始化认证状态，验证token有效性
  if (!authStore.initialized) {
    await authStore.initAuth()
  }
  
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresAdmin = to.matched.some(record => (record.meta as any).requiresAdmin)
  
  if (requiresAuth && !authStore.isLoggedIn) {
    next('/login')
  } else if (requiresAdmin && authStore.user?.role !== 'admin') {
    next('/home')
  } else if (to.path === '/login' && authStore.isLoggedIn) {
    // 如果已登录且访问登录页，重定向到首页
    next('/home')
  } else {
    // 设置页面标题
    if (to.meta.title) {
      document.title = `${to.meta.title} - 餐饮推荐系统`
    } else {
      document.title = '餐饮推荐系统'
    }
    next()
  }
})

export default router

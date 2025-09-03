import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器 - 添加认证token
api.interceptors.request.use(
  (config) => {
    // 从localStorage或其他地方获取token
    const token = localStorage.getItem('zishu_token') || 
                 sessionStorage.getItem('zishu_token') ||
                 getTokenFromCookie()
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // token过期或无效，跳转到登录页面
      console.warn('认证失败，请重新登录')
      // 这里可以触发重新登录流程
    }
    return Promise.reject(error)
  }
)

// 从cookie中获取token的辅助函数
function getTokenFromCookie(): string | null {
  if (typeof document === 'undefined') return null
  
  const cookies = document.cookie.split(';')
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=')
    if (name === 'atoken' || name === 'zishu_token') {
      return value
    }
  }
  return null
}

// 推荐相关API
export const recommendationAPI = {
  // 获取Top3推荐
  getTop3: (refresh = false) => {
    return api.get('/recommend/top3', {
      params: { refresh }
    })
  },

  // 提交用户反馈
  submitFeedback: (recommendationId: string, feedbackType: string) => {
    return api.post('/recommend/feedback', {
      recommendation_id: recommendationId,
      feedback_type: feedbackType
    })
  },

  // 获取推荐解释
  explainRecommendation: (recommendationId: string) => {
    return api.get(`/recommend/explain/${recommendationId}`)
  },

  // 健康检查
  healthCheck: () => {
    return api.get('/health')
  }
}

export default api
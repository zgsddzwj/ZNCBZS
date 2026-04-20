import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

/**
 * 请求拦截器
 * - 自动附加认证 token（如有）
 * - 记录请求日志（开发环境）
 */
api.interceptors.request.use(
  (config) => {
    // 自动附加 token
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // 开发环境打印请求信息
    if (import.meta.env.DEV) {
      console.log(
        `📤 ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`
      );
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * 响应拦截器
 * - 统一错误处理
 * - 401 自动跳转登录
 * - 网络错误友好提示
 */
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    const { response } = error;

    if (response) {
      const { status, data } = response;

      switch (status) {
        case 401:
          // 未授权，清除 token 并跳转登录页
          localStorage.removeItem("token");
          window.location.href = "/login";
          break;
        case 403:
          console.error("❌ 无权限访问该资源");
          break;
        case 404:
          console.error("❌ 请求的资源不存在");
          break;
        case 429:
          console.error("❌ 请求过于频繁，请稍后重试");
          break;
        default:
          if (status >= 500) {
            console.error(`❌ 服务器错误 (${status}): ${data?.detail || "未知错误"}`);
          }
      }
    } else {
      // 网络错误或超时
      console.error("❌ 网络连接失败，请检查网络后重试");
    }

    return Promise.reject(error);
  }
);

// ==================== API 接口 ====================

export async function chatQuery(data) {
  const response = await api.post("/chat/query", data);
  return response.data;
}

export async function getConversationHistory(conversationId) {
  const response = await api.get(`/chat/history/${conversationId}`);
  return response.data;
}

export async function clearConversationHistory(conversationId) {
  const response = await api.delete(`/chat/history/${conversationId}`);
  return response.data;
}

export default api;

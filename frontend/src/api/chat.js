import axios from "axios";
import { useAppStore } from "../stores/useAppStore";

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
 * - 自动触发全局Loading
 */
api.interceptors.request.use(
  (config) => {
    // 自动附加 token
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // 全局Loading: 排除聊天流式请求和轮询请求
    const skipLoading = config.skipGlobalLoading || config.url?.includes("/chat/query");
    if (!skipLoading) {
      useAppStore.getState().startLoading("请求中...");
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
    useAppStore.getState().stopLoading();
    return Promise.reject(error);
  }
);

/**
 * 响应拦截器
 * - 统一错误处理
 * - 401 自动跳转登录
 * - 网络错误友好提示
 * - 自动关闭全局Loading
 */
api.interceptors.response.use(
  (response) => {
    useAppStore.getState().stopLoading();
    return response;
  },
  (error) => {
    useAppStore.getState().stopLoading();

    const { response } = error;

    if (response) {
      const { status, data } = response;

      switch (status) {
        case 401:
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

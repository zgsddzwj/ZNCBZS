import axios from "axios";
import { useAppStore } from "../stores/useAppStore";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

// ===== 安全 Token 存储 =====
// access token 存储在内存中（XSS 无法读取），页面刷新后丢失
let _accessToken = null;
// refresh token 存储在 localStorage（仅用于刷新，不直接用于 API 请求）
const REFRESH_TOKEN_KEY = "refresh_token";

export function setTokens(accessToken, refreshToken) {
  _accessToken = accessToken;
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
}

export function clearTokens() {
  _accessToken = null;
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function getAccessToken() {
  return _accessToken;
}

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// 是否正在刷新 token（防止并发刷新）
let _isRefreshing = false;
let _refreshSubscribers = [];

function subscribeTokenRefresh(cb) {
  _refreshSubscribers.push(cb);
}

function onTokenRefreshed(token) {
  _refreshSubscribers.forEach((cb) => cb(token));
  _refreshSubscribers = [];
}

/**
 * 请求拦截器
 */
api.interceptors.request.use(
  (config) => {
    // 使用内存中的 access token
    if (_accessToken) {
      config.headers.Authorization = `Bearer ${_accessToken}`;
    }

    const skipLoading = config.skipGlobalLoading || config.url?.includes("/chat/query");
    if (!skipLoading) {
      useAppStore.getState().startLoading("请求中...");
    }

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
 * 响应拦截器 - 401 时自动刷新 token
 */
api.interceptors.response.use(
  (response) => {
    useAppStore.getState().stopLoading();
    return response;
  },
  async (error) => {
    useAppStore.getState().stopLoading();

    const originalRequest = error.config;
    const { response } = error;

    // 401 且未重试过 → 尝试刷新 token
    if (response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // 如果正在刷新，排队等待
      if (_isRefreshing) {
        return new Promise((resolve, reject) => {
          subscribeTokenRefresh((newToken) => {
            if (newToken) {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              resolve(api(originalRequest));
            } else {
              reject(error);
            }
          });
        });
      }

      _isRefreshing = true;
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

      if (!refreshToken) {
        _isRefreshing = false;
        clearTokens();
        window.location.href = "/login";
        return Promise.reject(error);
      }

      try {
        const res = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });
        const { access_token, refresh_token: newRefresh } = res.data;
        setTokens(access_token, newRefresh);
        _isRefreshing = false;
        onTokenRefreshed(access_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        _isRefreshing = false;
        _refreshSubscribers = [];
        clearTokens();
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }

    if (response) {
      const { status, data } = response;
      switch (status) {
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

export async function login(username, password) {
  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);
  const response = await api.post("/auth/login", formData, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  setTokens(response.data.access_token, response.data.refresh_token);
  return response.data;
}

export async function logout() {
  try {
    await api.post("/auth/logout");
  } finally {
    clearTokens();
  }
}

export default api;

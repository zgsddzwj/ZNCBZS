import { create } from 'zustand'

/**
 * 全局应用状态管理
 * - globalLoading: 全局加载状态（API请求时自动触发）
 * - loadingText: 加载提示文本
 * - setGlobalLoading: 设置加载状态
 * - withLoading: 包装异步操作，自动管理loading状态
 */
export const useAppStore = create((set, get) => ({
  // 状态
  globalLoading: false,
  loadingText: '加载中...',
  requestCount: 0, // 并发请求计数

  // Actions
  setGlobalLoading: (loading, text = '加载中...') => {
    set({ globalLoading: loading, loadingText: text })
  },

  startLoading: (text = '加载中...') => {
    const { requestCount } = get()
    set({
      requestCount: requestCount + 1,
      globalLoading: true,
      loadingText: text,
    })
  },

  stopLoading: () => {
    const { requestCount } = get()
    const newCount = Math.max(0, requestCount - 1)
    set({
      requestCount: newCount,
      globalLoading: newCount > 0,
    })
  },

  /**
   * 包装异步函数，自动管理loading状态
   * @param {Function} asyncFn - 异步函数
   * @param {string} text - loading提示文本
   */
  withLoading: async (asyncFn, text = '加载中...') => {
    get().startLoading(text)
    try {
      return await asyncFn()
    } finally {
      get().stopLoading()
    }
  },
}))

import React from 'react'
import { Spin } from 'antd'
import { useAppStore } from '../stores/useAppStore'

/**
 * 全局加载遮罩组件
 * 当有任何API请求进行时显示
 */
export default function GlobalLoading() {
  const { globalLoading, loadingText } = useAppStore()

  if (!globalLoading) return null

  return (
    <div className="global-loading-overlay">
      <div className="global-loading-content">
        <Spin size="large" />
        <p className="global-loading-text">{loadingText}</p>
      </div>
    </div>
  )
}

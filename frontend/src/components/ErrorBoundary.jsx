import React from 'react'
import { Result, Button } from 'antd'

/**
 * 全局错误边界组件
 * 捕获子组件树中的 JavaScript 错误，展示降级 UI
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('应用错误边界捕获到异常:', error, errorInfo)
    this.setState({ errorInfo })
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '48px', display: 'flex', justifyContent: 'center' }}>
          <Result
            status="error"
            title="页面发生错误"
            subTitle="抱歉，应用遇到了意外错误。请尝试刷新页面。"
            extra={[
              <Button type="primary" key="reload" onClick={this.handleReload}>
                返回首页
              </Button>,
              <Button
                key="refresh"
                onClick={() => window.location.reload()}
              >
                刷新页面
              </Button>,
            ]}
          />
        </div>
      )
    }
    return this.props.children
  }
}

export default ErrorBoundary

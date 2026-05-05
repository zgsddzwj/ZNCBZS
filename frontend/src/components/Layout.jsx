import React from 'react'
import { Layout as AntLayout, Menu, Breadcrumb } from 'antd'
import { useNavigate, useLocation, useMatches } from 'react-router-dom'
import {
  MessageOutlined,
  FileTextOutlined,
  BarChartOutlined,
  UploadOutlined,
  RobotOutlined,
  HomeOutlined,
} from '@ant-design/icons'

const { Header, Content, Sider, Footer } = AntLayout

// 页面路由映射（用于面包屑）
const ROUTE_MAP = {
  '/': { title: '对话查询', icon: <MessageOutlined /> },
  '/chat': { title: '对话查询', icon: <MessageOutlined /> },
  '/reports': { title: '财报管理', icon: <FileTextOutlined /> },
  '/analysis': { title: '深度分析', icon: <BarChartOutlined /> },
  '/agents': { title: '智能体应用', icon: <RobotOutlined /> },
  '/upload': { title: '上传财报', icon: <UploadOutlined /> },
}

const menuItems = [
  {
    key: '/chat',
    icon: <MessageOutlined />,
    label: '对话查询',
  },
  {
    key: '/reports',
    icon: <FileTextOutlined />,
    label: '财报管理',
  },
  {
    key: '/analysis',
    icon: <BarChartOutlined />,
    label: '深度分析',
  },
  {
    key: '/agents',
    icon: <RobotOutlined />,
    label: '智能体应用',
  },
  {
    key: '/upload',
    icon: <UploadOutlined />,
    label: '上传财报',
  },
]

export default function Layout({ children }) {
  const navigate = useNavigate()
  const location = useLocation()

  // 构建面包屑项
  const breadcrumbItems = [
    { title: <HomeOutlined />, href: '/' },
  ]

  const currentRoute = ROUTE_MAP[location.pathname]
  if (currentRoute) {
    breadcrumbItems.push({ title: currentRoute.title })
  }

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header className="app-header">
        <div className="header-left">
          <h1 className="app-title">智能财报助手</h1>
        </div>
        <div className="header-right">
          <span className="header-status">
            <span className="status-dot" />
            系统运行中
          </span>
        </div>
      </Header>
      <AntLayout>
        <Sider width={200} className="app-sider">
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
            style={{ height: '100%', borderRight: 0 }}
          />
        </Sider>
        <Layout>
          {/* 面包屑导航 */}
          <div className="breadcrumb-bar">
            <Breadcrumb items={breadcrumbItems} />
            <span className="breadcrumb-path">{location.pathname}</span>
          </div>
          <Content className="app-content">
            {children}
          </Content>
          {/* 页脚 */}
          <Footer className="app-footer">
            <span>智能财报助手 v1.0 &copy; {new Date().getFullYear()}</span>
            <span className="footer-divider">|</span>
            <span>基于大模型 + 知识增强的财务分析工具</span>
            <span className="footer-divider">|</span>
            <span className="footer-link">技术支持</span>
          </Footer>
        </Layout>
      </AntLayout>
    </AntLayout>
  )
}

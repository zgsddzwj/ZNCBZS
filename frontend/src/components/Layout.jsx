import React from 'react'
import { Layout as AntLayout, Menu } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  MessageOutlined,
  FileTextOutlined,
  BarChartOutlined,
  UploadOutlined,
  RobotOutlined,
} from '@ant-design/icons'

const { Header, Content, Sider } = AntLayout

export default function Layout({ children }) {
  const navigate = useNavigate()
  const location = useLocation()

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

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', color: '#fff', padding: '0 24px' }}>
        <h1 style={{ color: '#fff', margin: 0, lineHeight: '64px' }}>
          小京财智 AI 助手平台
        </h1>
      </Header>
      <AntLayout>
        <Sider width={200} style={{ background: '#fff' }}>
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
            style={{ height: '100%', borderRight: 0 }}
          />
        </Sider>
        <Content style={{ padding: '24px', background: '#fff' }}>
          {children}
        </Content>
      </AntLayout>
    </AntLayout>
  )
}


import React, { useState, useEffect } from 'react'
import { Card, List, Button, Modal, Form, Input, Select, Space, Tag, Row, Col, Statistic, Badge, Tooltip } from 'antd'
import {
  RobotOutlined,
  PlusOutlined,
  ThunderboltFilled,
  BarChartOutlined,
  FileTextOutlined,
  QuestionCircleOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  StarOutlined,
  StarFilled,
  AppstoreOutlined,
} from '@ant-design/icons'
import './AgentsPage.css'

const AGENT_ICONS = {
  boston_matrix: <BarChartOutlined />,
  swot: <FileTextOutlined />,
  credit_qa: <QuestionCircleOutlined />,
  retail_transformation: <BarChartOutlined />,
  document_writing: <FileTextOutlined />,
}

const AGENT_COLORS = {
  boston_matrix: { bg: 'rgba(26, 54, 93, 0.08)', icon: '#1a365d' },
  swot: { bg: 'rgba(44, 82, 130, 0.08)', icon: '#2c5282' },
  credit_qa: { bg: 'rgba(56, 161, 105, 0.08)', icon: '#38a169' },
  retail_transformation: { bg: 'rgba(212, 168, 83, 0.12)', icon: '#d4a853' },
  document_writing: { bg: 'rgba(49, 130, 206, 0.08)', icon: '#3182ce' },
}

export default function AgentsPage() {
  const [agents, setAgents] = useState([])
  const [loading, setLoading] = useState(false)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    loadAgents()
  }, [])

  const loadAgents = async () => {
    setLoading(true)
    try {
      setAgents([
        { id: 'boston_matrix', name: '波士顿矩阵助手', description: '自动生成波士顿矩阵图，划分业务类型并给出战略建议', category: '战略分析', usage: 128, status: 'active', rating: 4.8 },
        { id: 'swot', name: 'SWOT分析助手', description: '自动生成SWOT分析表及战略建议，支持多维度对比', category: '战略分析', usage: 96, status: 'active', rating: 4.6 },
        { id: 'credit_qa', name: '信贷问答助手', description: '解答信贷业务相关问题，基于政策库和案例库提供精准答案', category: '业务咨询', usage: 256, status: 'active', rating: 4.9 },
        { id: 'retail_transformation', name: '零售转型助手', description: '提供银行零售业务转型相关分析和最佳实践建议', category: '业务咨询', usage: 64, status: 'active', rating: 4.5 },
        { id: 'document_writing', name: '公文写作助手', description: '支持银行内部公文撰写，提供模板和智能润色功能', category: '办公效率', usage: 312, status: 'active', rating: 4.7 },
      ])
    } catch (error) {
      console.error('加载智能体失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateAgent = async (values) => {
    try {
      console.log('创建智能体:', values)
      setCreateModalVisible(false)
      form.resetFields()
      loadAgents()
    } catch (error) {
      console.error('创建智能体失败:', error)
    }
  }

  const getAgentIcon = (id) => AGENT_ICONS[id] || <RobotOutlined />
  const getAgentColors = (id) => AGENT_COLORS[id] || { bg: 'rgba(26, 54, 93, 0.08)', icon: '#1a365d' }

  const categories = [...new Set(agents.map(a => a.category))]

  return (
    <div className="agents-page">
      {/* 顶部统计 */}
      <Row gutter={[16, 16]} className="agents-stats">
        <Col xs={24} sm={12} md={6}>
          <Card className="agents-stat-card" bordered={false}>
            <div className="agents-stat-icon" style={{ background: 'rgba(26, 54, 93, 0.08)' }}>
              <AppstoreOutlined style={{ color: 'var(--primary)', fontSize: 24 }} />
            </div>
            <div className="agents-stat-info">
              <div className="agents-stat-value">{agents.length}</div>
              <div className="agents-stat-label">智能体总数</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="agents-stat-card" bordered={false}>
            <div className="agents-stat-icon" style={{ background: 'rgba(56, 161, 105, 0.08)' }}>
              <CheckCircleOutlined style={{ color: 'var(--success)', fontSize: 24 }} />
            </div>
            <div className="agents-stat-info">
              <div className="agents-stat-value" style={{ color: 'var(--success)' }}>
                {agents.filter(a => a.status === 'active').length}
              </div>
              <div className="agents-stat-label">运行中</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="agents-stat-card" bordered={false}>
            <div className="agents-stat-icon" style={{ background: 'rgba(212, 168, 83, 0.12)' }}>
              <ThunderboltFilled style={{ color: 'var(--accent)', fontSize: 24 }} />
            </div>
            <div className="agents-stat-info">
              <div className="agents-stat-value" style={{ color: 'var(--accent)' }}>
                {agents.reduce((sum, a) => sum + a.usage, 0)}
              </div>
              <div className="agents-stat-label">总调用次数</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="agents-stat-card" bordered={false}>
            <div className="agents-stat-icon" style={{ background: 'rgba(49, 130, 206, 0.08)' }}>
              <StarFilled style={{ color: 'var(--info)', fontSize: 24 }} />
            </div>
            <div className="agents-stat-info">
              <div className="agents-stat-value" style={{ color: 'var(--info)' }}>
                {(agents.reduce((sum, a) => sum + a.rating, 0) / (agents.length || 1)).toFixed(1)}
              </div>
              <div className="agents-stat-label">平均评分</div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 分类标签 */}
      <div className="agents-category-bar">
        <Tag className="category-tag active">全部</Tag>
        {categories.map(cat => (
          <Tag key={cat} className="category-tag">{cat}</Tag>
        ))}
      </div>

      {/* 智能体卡片网格 */}
      <Row gutter={[16, 16]} className="agents-grid">
        {agents.map((agent) => {
          const colors = getAgentColors(agent.id)
          return (
            <Col xs={24} sm={12} lg={8} key={agent.id}>
              <Card
                className="agent-card"
                bordered={false}
                hoverable
                actions={[
                  <Tooltip title="使用" key="use">
                    <Button type="text" icon={<EyeOutlined />} className="agent-action-btn">使用</Button>
                  </Tooltip>,
                  <Tooltip title="编辑" key="edit">
                    <Button type="text" icon={<EditOutlined />} className="agent-action-btn">编辑</Button>
                  </Tooltip>,
                  <Tooltip title="删除" key="delete">
                    <Button type="text" icon={<DeleteOutlined />} className="agent-action-btn danger">删除</Button>
                  </Tooltip>,
                ]}
              >
                <div className="agent-card-header">
                  <div
                    className="agent-icon-wrapper"
                    style={{ background: colors.bg }}
                  >
                    <span style={{ color: colors.icon, fontSize: 24 }}>
                      {getAgentIcon(agent.id)}
                    </span>
                  </div>
                  <div className="agent-status">
                    <Badge status="success" text="运行中" />
                  </div>
                </div>
                <div className="agent-card-body">
                  <h3 className="agent-name">{agent.name}</h3>
                  <p className="agent-description">{agent.description}</p>
                  <div className="agent-meta">
                    <Tag className="agent-category-tag">{agent.category}</Tag>
                    <div className="agent-rating">
                      <StarFilled style={{ color: '#d4a853', fontSize: 12 }} />
                      <span>{agent.rating}</span>
                    </div>
                  </div>
                </div>
                <div className="agent-card-footer">
                  <div className="agent-usage">
                    <ThunderboltFilled style={{ color: 'var(--accent)', fontSize: 12 }} />
                    <span>{agent.usage} 次调用</span>
                  </div>
                  <div className="agent-time">
                    <ClockCircleOutlined style={{ fontSize: 12 }} />
                    <span>最近使用 2小时前</span>
                  </div>
                </div>
              </Card>
            </Col>
          )
        })}

        {/* 创建卡片 */}
        <Col xs={24} sm={12} lg={8}>
          <Card
            className="agent-create-card"
            bordered={false}
            onClick={() => setCreateModalVisible(true)}
          >
            <div className="agent-create-content">
              <div className="agent-create-icon">
                <PlusOutlined />
              </div>
              <h3 className="agent-create-title">创建自定义智能体</h3>
              <p className="agent-create-desc">根据您的业务需求，配置专属的智能分析助手</p>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 创建模态框 */}
      <Modal
        title={
          <div className="agent-modal-title">
            <RobotOutlined />
            <span>创建自定义智能体</span>
          </div>
        }
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false)
          form.resetFields()
        }}
        onOk={() => form.submit()}
        okText="创建"
        cancelText="取消"
        className="agent-modal"
        width={560}
      >
        <Form form={form} onFinish={handleCreateAgent} layout="vertical" className="agent-form">
          <Form.Item name="name" label="智能体名称" rules={[{ required: true, message: '请输入智能体名称' }]}>
            <Input placeholder="例如：财报摘要助手" prefix={<RobotOutlined />} className="agent-form-input" />
          </Form.Item>
          <Form.Item name="description" label="功能描述" rules={[{ required: true, message: '请输入功能描述' }]}>
            <Input.TextArea
              rows={3}
              placeholder="描述智能体的功能和应用场景，例如：自动提取财报关键指标并生成摘要..."
              className="agent-form-textarea"
            />
          </Form.Item>
          <Form.Item name="category" label="所属分类">
            <Select placeholder="选择分类" className="agent-form-select">
              <Select.Option value="战略分析">战略分析</Select.Option>
              <Select.Option value="业务咨询">业务咨询</Select.Option>
              <Select.Option value="办公效率">办公效率</Select.Option>
              <Select.Option value="数据分析">数据分析</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="knowledge_base" label="关联知识库">
            <Select placeholder="选择知识库" allowClear className="agent-form-select">
              <Select.Option value="credit_policy">信贷政策库</Select.Option>
              <Select.Option value="retail_transformation">零售转型案例库</Select.Option>
              <Select.Option value="financial_report">财报知识库</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="capabilities" label="功能配置">
            <Select mode="multiple" placeholder="选择功能" className="agent-form-select">
              <Select.Option value="qa">问答交互</Select.Option>
              <Select.Option value="report">报告生成</Select.Option>
              <Select.Option value="query">数据查询</Select.Option>
              <Select.Option value="chart">图表生成</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

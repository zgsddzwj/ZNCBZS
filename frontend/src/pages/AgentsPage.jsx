import React, { useState, useEffect } from 'react'
import { Card, List, Button, Modal, Form, Input, Select, Space, Tag } from 'antd'
import { RobotOutlined, PlusOutlined } from '@ant-design/icons'

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
      // 调用API获取智能体列表
      // const response = await fetch('/api/v1/agents/list')
      // const data = await response.json()
      // setAgents(data.agents || [])
      
      // 模拟数据
      setAgents([
        { id: 'boston_matrix', name: '波士顿矩阵助手', description: '自动生成波士顿矩阵图，划分业务类型并给出建议' },
        { id: 'swot', name: 'SWOT分析助手', description: '自动生成SWOT分析表及战略建议' },
        { id: 'credit_qa', name: '信贷问答助手', description: '解答信贷业务相关问题' },
        { id: 'retail_transformation', name: '零售转型助手', description: '提供银行零售业务转型相关分析' },
        { id: 'document_writing', name: '公文写作助手', description: '支持银行内部公文撰写' },
      ])
    } catch (error) {
      console.error('加载智能体失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateAgent = async (values) => {
    try {
      // 调用API创建智能体
      // await fetch('/api/v1/agents/create', { ... })
      console.log('创建智能体:', values)
      setCreateModalVisible(false)
      form.resetFields()
      loadAgents()
    } catch (error) {
      console.error('创建智能体失败:', error)
    }
  }

  return (
    <div>
      <Card
        title="智能体应用"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            创建智能体
          </Button>
        }
      >
        <List
          loading={loading}
          dataSource={agents}
          renderItem={(agent) => (
            <List.Item
              actions={[
                <Button type="link">使用</Button>,
                <Button type="link">编辑</Button>,
              ]}
            >
              <List.Item.Meta
                avatar={<RobotOutlined style={{ fontSize: 24 }} />}
                title={agent.name}
                description={agent.description}
              />
            </List.Item>
          )}
        />
      </Card>

      <Modal
        title="创建自定义智能体"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false)
          form.resetFields()
        }}
        onOk={() => form.submit()}
      >
        <Form form={form} onFinish={handleCreateAgent} layout="vertical">
          <Form.Item name="name" label="智能体名称" rules={[{ required: true }]}>
            <Input placeholder="输入智能体名称" />
          </Form.Item>
          <Form.Item name="description" label="功能描述" rules={[{ required: true }]}>
            <Input.TextArea rows={3} placeholder="描述智能体的功能和应用场景" />
          </Form.Item>
          <Form.Item name="knowledge_base" label="关联知识库">
            <Select placeholder="选择知识库" allowClear>
              <Select.Option value="credit_policy">信贷政策库</Select.Option>
              <Select.Option value="retail_transformation">零售转型案例库</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="capabilities" label="功能配置">
            <Select mode="multiple" placeholder="选择功能">
              <Select.Option value="qa">问答交互</Select.Option>
              <Select.Option value="report">报告生成</Select.Option>
              <Select.Option value="query">数据查询</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}


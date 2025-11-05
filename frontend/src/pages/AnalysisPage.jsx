import React, { useState } from 'react'
import { Card, Tabs, Form, Input, Button, Select, Space } from 'antd'
import ReactECharts from 'echarts-for-react'

const { TabPane } = Tabs

export default function AnalysisPage() {
  const [form] = Form.useForm()

  const handleAnalysis = (values) => {
    console.log('分析参数:', values)
    // 调用分析API
  }

  const chartOption = {
    title: { text: '趋势分析' },
    xAxis: { type: 'category', data: ['2020', '2021', '2022', '2023'] },
    yAxis: { type: 'value' },
    series: [{ data: [120, 132, 101, 134], type: 'line' }],
  }

  return (
    <Card title="深度分析">
      <Tabs defaultActiveKey="trend">
        <TabPane tab="趋势分析" key="trend">
          <Form form={form} onFinish={handleAnalysis} layout="inline">
            <Form.Item name="company" label="公司">
              <Input placeholder="输入公司名称" />
            </Form.Item>
            <Form.Item name="indicator" label="指标">
              <Select placeholder="选择指标" style={{ width: 150 }}>
                <Select.Option value="营收">营收</Select.Option>
                <Select.Option value="净利润">净利润</Select.Option>
                <Select.Option value="ROE">ROE</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit">
                分析
              </Button>
            </Form.Item>
          </Form>
          <div style={{ marginTop: 24 }}>
            <ReactECharts option={chartOption} style={{ height: 400 }} />
          </div>
        </TabPane>
        <TabPane tab="归因分析" key="attribution">
          <p>归因分析功能开发中...</p>
        </TabPane>
        <TabPane tab="风险分析" key="risk">
          <p>风险分析功能开发中...</p>
        </TabPane>
        <TabPane tab="行业对标" key="industry">
          <p>行业对标功能开发中...</p>
        </TabPane>
      </Tabs>
    </Card>
  )
}


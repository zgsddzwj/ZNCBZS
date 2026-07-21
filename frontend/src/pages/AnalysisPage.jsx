import React, { useState } from 'react'
import { Card, Tabs, Form, Input, Button, Select, Space, Row, Col, Statistic, Tag, Badge } from 'antd'
import {
  LineChartOutlined,
  PieChartOutlined,
  WarningOutlined,
  BarChartOutlined,
  SearchOutlined,
  RiseOutlined,
  FallOutlined,
  AimOutlined,
  BankOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import './AnalysisPage.css'

const { TabPane } = Tabs

export default function AnalysisPage() {
  const [form] = Form.useForm()
  const [activeTab, setActiveTab] = useState('trend')
  const [analyzing, setAnalyzing] = useState(false)

  const handleAnalysis = (values) => {
    setAnalyzing(true)
    console.log('分析参数:', values)
    setTimeout(() => setAnalyzing(false), 1500)
  }

  const chartOption = {
    backgroundColor: 'transparent',
    title: {
      text: '营收趋势分析',
      left: 'center',
      textStyle: { color: '#1a202c', fontSize: 16, fontWeight: 600 },
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#1a202c' },
      axisPointer: {
        type: 'cross',
        crossStyle: { color: '#999' },
      },
    },
    legend: {
      data: ['营收(亿元)', '同比增长率'],
      bottom: 0,
      textStyle: { color: '#4a5568' },
    },
    grid: { left: '3%', right: '4%', bottom: '12%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: ['2020', '2021', '2022', '2023', '2024E'],
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#718096' },
    },
    yAxis: [
      {
        type: 'value',
        name: '营收(亿元)',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#718096' },
        splitLine: { lineStyle: { color: '#edf2f7', type: 'dashed' } },
      },
      {
        type: 'value',
        name: '增长率',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#718096', formatter: '{value}%' },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '营收(亿元)',
        type: 'bar',
        data: [120, 145, 132, 168, 185],
        itemStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: '#2c5282' },
              { offset: 1, color: '#1a365d' },
            ],
          },
          borderRadius: [6, 6, 0, 0],
        },
        barWidth: '40%',
      },
      {
        name: '同比增长率',
        type: 'line',
        yAxisIndex: 1,
        data: [8, 20.8, -9, 27.3, 10.1],
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { color: '#d4a853', width: 3 },
        itemStyle: { color: '#d4a853', borderWidth: 2, borderColor: '#fff' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(212, 168, 83, 0.2)' },
              { offset: 1, color: 'rgba(212, 168, 83, 0)' },
            ],
          },
        },
      },
    ],
  }

  const pieOption = {
    backgroundColor: 'transparent',
    title: {
      text: '业务结构占比',
      left: 'center',
      textStyle: { color: '#1a202c', fontSize: 16, fontWeight: 600 },
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#1a202c' },
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      textStyle: { color: '#4a5568' },
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '55%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: { show: false },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
            color: '#1a202c',
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.1)',
          },
        },
        data: [
          { value: 45, name: '零售业务', itemStyle: { color: '#1a365d' } },
          { value: 30, name: '对公业务', itemStyle: { color: '#2c5282' } },
          { value: 15, name: '同业业务', itemStyle: { color: '#4a7ab8' } },
          { value: 10, name: '其他', itemStyle: { color: '#d4a853' } },
        ],
      },
    ],
  }

  const tabItems = [
    { key: 'trend', label: '趋势分析', icon: <LineChartOutlined /> },
    { key: 'attribution', label: '归因分析', icon: <PieChartOutlined /> },
    { key: 'risk', label: '风险分析', icon: <WarningOutlined /> },
    { key: 'industry', label: '行业对标', icon: <BarChartOutlined /> },
  ]

  return (
    <div className="analysis-page">
      {/* 分析指标概览 */}
      <Row gutter={[16, 16]} className="analysis-stats">
        <Col xs={24} sm={12} md={6}>
          <Card className="analysis-stat-card" bordered={false}>
            <div className="analysis-stat-icon" style={{ background: 'rgba(26, 54, 93, 0.08)' }}>
              <RiseOutlined style={{ color: 'var(--primary)', fontSize: 24 }} />
            </div>
            <div className="analysis-stat-info">
              <div className="analysis-stat-value">+18.5%</div>
              <div className="analysis-stat-label">营收增长率</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="analysis-stat-card" bordered={false}>
            <div className="analysis-stat-icon" style={{ background: 'rgba(56, 161, 105, 0.08)' }}>
              <AimOutlined style={{ color: 'var(--success)', fontSize: 24 }} />
            </div>
            <div className="analysis-stat-info">
              <div className="analysis-stat-value" style={{ color: 'var(--success)' }}>12.3%</div>
              <div className="analysis-stat-label">ROE</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="analysis-stat-card" bordered={false}>
            <div className="analysis-stat-icon" style={{ background: 'rgba(212, 168, 83, 0.12)' }}>
              <BankOutlined style={{ color: 'var(--accent)', fontSize: 24 }} />
            </div>
            <div className="analysis-stat-info">
              <div className="analysis-stat-value" style={{ color: 'var(--accent)' }}>2.85</div>
              <div className="analysis-stat-label">PB 估值</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="analysis-stat-card" bordered={false}>
            <div className="analysis-stat-icon" style={{ background: 'rgba(229, 62, 62, 0.06)' }}>
              <FallOutlined style={{ color: 'var(--error)', fontSize: 24 }} />
            </div>
            <div className="analysis-stat-info">
              <div className="analysis-stat-value" style={{ color: 'var(--error)' }}>1.12%</div>
              <div className="analysis-stat-label">不良率</div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 分析面板 */}
      <Card className="analysis-panel-card">
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          className="analysis-tabs"
          items={tabItems.map(item => ({
            key: item.key,
            label: (
              <span className="analysis-tab-label">
                {item.icon}
                {item.label}
              </span>
            ),
            children: null,
          }))}
        />

        <div className="analysis-content">
          {activeTab === 'trend' && (
            <div className="analysis-section animate-fade-in">
              <div className="analysis-form-bar">
                <Form form={form} onFinish={handleAnalysis} layout="inline" className="analysis-form">
                  <Form.Item name="company" label="公司">
                    <Input placeholder="输入公司名称" prefix={<BankOutlined />} className="analysis-input" />
                  </Form.Item>
                  <Form.Item name="indicator" label="指标">
                    <Select placeholder="选择指标" className="analysis-select">
                      <Select.Option value="营收">营收</Select.Option>
                      <Select.Option value="净利润">净利润</Select.Option>
                      <Select.Option value="ROE">ROE</Select.Option>
                      <Select.Option value="不良率">不良率</Select.Option>
                    </Select>
                  </Form.Item>
                  <Form.Item name="period" label="周期">
                    <Select placeholder="选择周期" defaultValue="annual" className="analysis-select">
                      <Select.Option value="annual">年度</Select.Option>
                      <Select.Option value="quarterly">季度</Select.Option>
                    </Select>
                  </Form.Item>
                  <Form.Item>
                    <Button
                      type="primary"
                      icon={<SearchOutlined />}
                      htmlType="submit"
                      loading={analyzing}
                      className="analysis-btn"
                    >
                      开始分析
                    </Button>
                  </Form.Item>
                </Form>
              </div>

              <Row gutter={[16, 16]}>
                <Col xs={24} lg={16}>
                  <Card className="chart-card" title="趋势图表" bordered={false}>
                    <ReactECharts option={chartOption} style={{ height: 400 }} />
                  </Card>
                </Col>
                <Col xs={24} lg={8}>
                  <Card className="chart-card" title="结构占比" bordered={false}>
                    <ReactECharts option={pieOption} style={{ height: 400 }} />
                  </Card>
                </Col>
              </Row>

              <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
                <Col xs={24} md={8}>
                  <Card className="insight-card" bordered={false}>
                    <div className="insight-header">
                      <RiseOutlined style={{ color: 'var(--success)' }} />
                      <span>增长亮点</span>
                    </div>
                    <p className="insight-text">2023年营收同比增长 27.3%，主要受益于零售业务扩张及数字化转型成效显著。</p>
                  </Card>
                </Col>
                <Col xs={24} md={8}>
                  <Card className="insight-card" bordered={false}>
                    <div className="insight-header">
                      <WarningOutlined style={{ color: 'var(--warning)' }} />
                      <span>关注要点</span>
                    </div>
                    <p className="insight-text">2022年营收出现短暂下滑，需关注宏观经济波动对业绩的周期性影响。</p>
                  </Card>
                </Col>
                <Col xs={24} md={8}>
                  <Card className="insight-card" bordered={false}>
                    <div className="insight-header">
                      <AimOutlined style={{ color: 'var(--primary)' }} />
                      <span>预测展望</span>
                    </div>
                    <p className="insight-text">预计2024年营收将达到185亿元，同比增长约10%，增速趋于稳健。</p>
                  </Card>
                </Col>
              </Row>
            </div>
          )}

          {activeTab === 'attribution' && (
            <div className="analysis-section animate-fade-in">
              <div className="placeholder-content">
                <PieChartOutlined className="placeholder-icon" />
                <h3>归因分析</h3>
                <p>分析各因素对业绩变动的贡献度，识别核心驱动因素</p>
                <Tag color="blue">功能开发中</Tag>
              </div>
            </div>
          )}

          {activeTab === 'risk' && (
            <div className="analysis-section animate-fade-in">
              <div className="placeholder-content">
                <WarningOutlined className="placeholder-icon" />
                <h3>风险分析</h3>
                <p>评估信用风险、市场风险、操作风险等多维度风险指标</p>
                <Tag color="orange">功能开发中</Tag>
              </div>
            </div>
          )}

          {activeTab === 'industry' && (
            <div className="analysis-section animate-fade-in">
              <div className="placeholder-content">
                <BarChartOutlined className="placeholder-icon" />
                <h3>行业对标</h3>
                <p>与同业公司进行多维度对比分析，发现竞争优势与差距</p>
                <Tag color="green">功能开发中</Tag>
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}

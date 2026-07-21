import React, { useState } from 'react'
import { Card, Table, Input, Button, Select, Space, Statistic, Row, Col, Tag, Badge } from 'antd'
import {
  SearchOutlined,
  FileTextOutlined,
  CloudUploadOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  EyeOutlined,
  DownloadOutlined,
} from '@ant-design/icons'
import './ReportPage.css'

export default function ReportPage() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState([])
  const [searchValue, setSearchValue] = useState('')

  const columns = [
    {
      title: '公司名称',
      dataIndex: 'company',
      key: 'company',
      render: (text) => (
        <span className="report-company">
          <FileTextOutlined style={{ color: 'var(--primary)', marginRight: 8 }} />
          <strong>{text}</strong>
        </span>
      ),
    },
    {
      title: '年份',
      dataIndex: 'year',
      key: 'year',
      render: (year) => (
        <Tag color="default" className="report-year-tag">
          {year}
        </Tag>
      ),
      width: 100,
    },
    {
      title: '报告类型',
      dataIndex: 'report_type',
      key: 'report_type',
      render: (type) => {
        const typeMap = {
          annual: { color: 'blue', label: '年报' },
          quarterly: { color: 'cyan', label: '季报' },
          'semi-annual': { color: 'geekblue', label: '半年报' },
        }
        const t = typeMap[type] || { color: 'default', label: type }
        return <Tag color={t.color} className="report-type-tag">{t.label}</Tag>
      },
      width: 120,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const statusMap = {
          processed: { status: 'success', text: '已解析' },
          pending: { status: 'processing', text: '处理中' },
          failed: { status: 'error', text: '失败' },
        }
        const s = statusMap[status] || { status: 'default', text: status }
        return <Badge status={s.status} text={s.text} />
      },
      width: 120,
    },
    {
      title: '上传时间',
      dataIndex: 'upload_time',
      key: 'upload_time',
      render: (time) => (
        <span className="report-time">
          <ClockCircleOutlined style={{ marginRight: 4, color: 'var(--text-muted)' }} />
          {time}
        </span>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button
            type="text"
            icon={<EyeOutlined />}
            className="report-action-btn"
          >
            查看
          </Button>
          <Button
            type="text"
            icon={<DownloadOutlined />}
            className="report-action-btn"
          >
            下载
          </Button>
        </Space>
      ),
      width: 180,
    },
  ]

  // 模拟数据
  const demoData = [
    { id: '1', company: '贵州茅台', year: '2023', report_type: 'annual', status: 'processed', upload_time: '2024-01-15 09:30' },
    { id: '2', company: '招商银行', year: '2023', report_type: 'annual', status: 'processed', upload_time: '2024-01-14 14:20' },
    { id: '3', company: '工商银行', year: '2023', report_type: 'quarterly', status: 'pending', upload_time: '2024-01-16 10:00' },
    { id: '4', company: '建设银行', year: '2022', report_type: 'annual', status: 'processed', upload_time: '2024-01-10 16:45' },
    { id: '5', company: '中国平安', year: '2023', report_type: 'semi-annual', status: 'failed', upload_time: '2024-01-12 11:30' },
  ]

  return (
    <div className="report-page">
      {/* 统计卡片 */}
      <Row gutter={[16, 16]} className="report-stats">
        <Col xs={24} sm={12} md={8} lg={6}>
          <Card className="stat-card" bordered={false}>
            <Statistic
              title="总报告数"
              value={128}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: 'var(--primary)', fontWeight: 700 }}
            />
            <div className="stat-trend">+12 本月新增</div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={6}>
          <Card className="stat-card" bordered={false}>
            <Statistic
              title="已解析"
              value={115}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: 'var(--success)', fontWeight: 700 }}
            />
            <div className="stat-trend success">解析率 89.8%</div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={6}>
          <Card className="stat-card" bordered={false}>
            <Statistic
              title="处理中"
              value={8}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: 'var(--warning)', fontWeight: 700 }}
            />
            <div className="stat-trend warning">预计 5 分钟完成</div>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={6}>
          <Card className="stat-card" bordered={false}>
            <Statistic
              title="本月上传"
              value={23}
              prefix={<CloudUploadOutlined />}
              valueStyle={{ color: 'var(--accent)', fontWeight: 700 }}
            />
            <div className="stat-trend accent">+5 较上周</div>
          </Card>
        </Col>
      </Row>

      {/* 数据表格 */}
      <Card
        title={
          <div className="report-table-header">
            <span className="report-table-title">财报列表</span>
            <span className="report-table-count">共 {demoData.length} 条记录</span>
          </div>
        }
        className="report-table-card"
        extra={
          <Button type="primary" icon={<CloudUploadOutlined />}>
            上传财报
          </Button>
        }
      >
        <div className="report-toolbar">
          <Input
            placeholder="搜索公司名称..."
            prefix={<SearchOutlined style={{ color: 'var(--text-muted)' }} />}
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            className="report-search-input"
            allowClear
          />
          <Select
            placeholder="选择年份"
            className="report-filter-select"
            allowClear
          >
            <Select.Option value="2024">2024</Select.Option>
            <Select.Option value="2023">2023</Select.Option>
            <Select.Option value="2022">2022</Select.Option>
          </Select>
          <Select
            placeholder="报告类型"
            className="report-filter-select"
            allowClear
          >
            <Select.Option value="annual">年报</Select.Option>
            <Select.Option value="quarterly">季报</Select.Option>
            <Select.Option value="semi-annual">半年报</Select.Option>
          </Select>
          <Button type="primary" icon={<SearchOutlined />}>
            搜索
          </Button>
        </div>
        <Table
          columns={columns}
          dataSource={demoData}
          loading={loading}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
          className="report-table"
        />
      </Card>
    </div>
  )
}

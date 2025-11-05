import React, { useState } from 'react'
import { Card, Table, Input, Button, Select, Space } from 'antd'
import { SearchOutlined } from '@ant-design/icons'

export default function ReportPage() {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState([])

  const columns = [
    {
      title: '公司名称',
      dataIndex: 'company',
      key: 'company',
    },
    {
      title: '年份',
      dataIndex: 'year',
      key: 'year',
    },
    {
      title: '报告类型',
      dataIndex: 'report_type',
      key: 'report_type',
    },
    {
      title: '上传时间',
      dataIndex: 'upload_time',
      key: 'upload_time',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button type="link">查看</Button>
          <Button type="link">下载</Button>
        </Space>
      ),
    },
  ]

  return (
    <Card title="财报管理">
      <Space style={{ marginBottom: 16 }}>
        <Input placeholder="搜索公司..." style={{ width: 200 }} />
        <Select placeholder="选择年份" style={{ width: 120 }} allowClear>
          <Select.Option value="2023">2023</Select.Option>
          <Select.Option value="2022">2022</Select.Option>
        </Select>
        <Button type="primary" icon={<SearchOutlined />}>
          搜索
        </Button>
      </Space>
      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />
    </Card>
  )
}


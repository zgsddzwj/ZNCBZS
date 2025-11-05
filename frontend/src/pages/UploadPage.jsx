import React, { useState } from 'react'
import { Card, Upload, Button, Form, Input, Select, message } from 'antd'
import { UploadOutlined } from '@ant-design/icons'

export default function UploadPage() {
  const [form] = Form.useForm()
  const [fileList, setFileList] = useState([])
  const [uploading, setUploading] = useState(false)

  const handleUpload = async (values) => {
    if (fileList.length === 0) {
      message.warning('请先选择文件')
      return
    }

    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', fileList[0])
      formData.append('company', values.company)
      formData.append('year', values.year)
      formData.append('report_type', values.report_type)

      // 调用上传API
      // const response = await uploadReport(formData)
      message.success('上传成功')
      form.resetFields()
      setFileList([])
    } catch (error) {
      message.error('上传失败')
    } finally {
      setUploading(false)
    }
  }

  return (
    <Card title="上传财报">
      <Form form={form} onFinish={handleUpload} layout="vertical">
        <Form.Item
          name="file"
          label="选择文件"
          rules={[{ required: true, message: '请选择文件' }]}
        >
          <Upload
            fileList={fileList}
            onChange={({ fileList }) => setFileList(fileList)}
            beforeUpload={() => false}
            accept=".pdf,.docx,.doc,.xlsx,.xls"
          >
            <Button icon={<UploadOutlined />}>选择文件</Button>
          </Upload>
          <p style={{ color: '#999', marginTop: 8 }}>
            支持格式：PDF、Word、Excel
          </p>
        </Form.Item>
        <Form.Item name="company" label="公司名称">
          <Input placeholder="输入公司名称" />
        </Form.Item>
        <Form.Item name="year" label="年份">
          <Input placeholder="输入年份，如：2023" />
        </Form.Item>
        <Form.Item name="report_type" label="报告类型" initialValue="annual">
          <Select>
            <Select.Option value="annual">年报</Select.Option>
            <Select.Option value="quarterly">季报</Select.Option>
            <Select.Option value="semi-annual">半年报</Select.Option>
          </Select>
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={uploading}>
            上传并解析
          </Button>
        </Form.Item>
      </Form>
    </Card>
  )
}


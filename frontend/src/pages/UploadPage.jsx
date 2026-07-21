import React, { useState } from 'react'
import { Card, Upload, Button, Form, Input, Select, message, Progress, Steps, Row, Col, List, Tag } from 'antd'
import {
  UploadOutlined,
  CloudUploadOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FileExcelOutlined,
  FileUnknownOutlined,
  CheckCircleOutlined,
  InboxOutlined,
  DeleteOutlined,
  FileTextOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons'
import './UploadPage.css'

export default function UploadPage() {
  const [form] = Form.useForm()
  const [fileList, setFileList] = useState([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [currentStep, setCurrentStep] = useState(0)

  const handleUpload = async (values) => {
    if (fileList.length === 0) {
      message.warning('请先选择文件')
      return
    }

    setUploading(true)
    setCurrentStep(1)
    setUploadProgress(0)

    // 模拟上传进度
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 90) {
          clearInterval(interval)
          return 90
        }
        return prev + 10
      })
    }, 200)

    try {
      const formData = new FormData()
      formData.append('file', fileList[0])
      formData.append('company', values.company)
      formData.append('year', values.year)
      formData.append('report_type', values.report_type)

      // 调用上传API
      // const response = await uploadReport(formData)

      setTimeout(() => {
        clearInterval(interval)
        setUploadProgress(100)
        setCurrentStep(2)
        message.success('上传成功！文件正在解析中...')
        form.resetFields()
        setFileList([])
        setUploading(false)
        setTimeout(() => setCurrentStep(0), 3000)
      }, 2000)
    } catch (error) {
      clearInterval(interval)
      message.error('上传失败')
      setUploading(false)
      setCurrentStep(0)
    }
  }

  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop().toLowerCase()
    if (ext === 'pdf') return <FilePdfOutlined className="file-icon pdf" />
    if (['doc', 'docx'].includes(ext)) return <FileWordOutlined className="file-icon word" />
    if (['xls', 'xlsx'].includes(ext)) return <FileExcelOutlined className="file-icon excel" />
    return <FileUnknownOutlined className="file-icon" />
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return ''
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
  }

  const steps = [
    { title: '选择文件', icon: <InboxOutlined /> },
    { title: '上传中', icon: <CloudUploadOutlined /> },
    { title: '解析完成', icon: <CheckCircleOutlined /> },
  ]

  const recentUploads = [
    { id: '1', name: '贵州茅台_2023_年报.pdf', size: '3.2 MB', status: 'success', time: '2分钟前' },
    { id: '2', name: '招商银行_2023_年报.pdf', size: '2.8 MB', status: 'success', time: '15分钟前' },
    { id: '3', name: '工商银行_2023_Q3季报.pdf', size: '1.5 MB', status: 'processing', time: '刚刚' },
  ]

  return (
    <div className="upload-page">
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          <Card
            className="upload-main-card"
            title={
              <div className="upload-card-header">
                <CloudUploadOutlined className="upload-card-icon" />
                <span>上传财报文件</span>
              </div>
            }
          >
            <Steps
              current={currentStep}
              items={steps}
              className="upload-steps"
            />

            <Form form={form} onFinish={handleUpload} layout="vertical" className="upload-form">
              <Form.Item
                name="file"
                label="选择文件"
                rules={[{ required: true, message: '请选择文件' }]}
              >
                <Upload.Dragger
                  fileList={fileList}
                  onChange={({ fileList }) => setFileList(fileList.slice(-1))}
                  beforeUpload={() => false}
                  accept=".pdf,.docx,.doc,.xlsx,.xls"
                  multiple={false}
                  className="upload-dragger"
                >
                  <div className="upload-dragger-content">
                    <div className="upload-dragger-icon">
                      <InboxOutlined />
                    </div>
                    <p className="upload-dragger-title">点击或拖拽文件至此处上传</p>
                    <p className="upload-dragger-hint">
                      支持 PDF、Word、Excel 格式，单个文件不超过 100MB
                    </p>
                  </div>
                </Upload.Dragger>
              </Form.Item>

              {fileList.length > 0 && (
                <div className="file-preview-card animate-fade-in">
                  <div className="file-preview-info">
                    {getFileIcon(fileList[0].name)}
                    <div className="file-preview-detail">
                      <div className="file-preview-name">{fileList[0].name}</div>
                      <div className="file-preview-meta">
                        <span>{formatFileSize(fileList[0].size)}</span>
                        <Tag size="small" className="file-preview-tag">待上传</Tag>
                      </div>
                    </div>
                  </div>
                  <Button
                    type="text"
                    icon={<DeleteOutlined />}
                    onClick={() => setFileList([])}
                    className="file-preview-delete"
                    danger
                  />
                </div>
              )}

              {uploading && (
                <div className="upload-progress animate-fade-in">
                  <Progress
                    percent={uploadProgress}
                    status={uploadProgress === 100 ? 'success' : 'active'}
                    strokeColor={{
                      '0%': '#1a365d',
                      '100%': '#d4a853',
                    }}
                    showInfo={true}
                  />
                  <div className="upload-progress-text">
                    {uploadProgress < 100 ? '正在上传文件...' : '上传完成，正在解析...'}
                  </div>
                </div>
              )}

              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item name="company" label="公司名称">
                    <Input placeholder="输入公司名称" prefix={<FileTextOutlined />} className="upload-input" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item name="year" label="年份">
                    <Input placeholder="输入年份，如：2023" prefix={<SafetyCertificateOutlined />} className="upload-input" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item name="report_type" label="报告类型" initialValue="annual">
                <Select className="upload-select">
                  <Select.Option value="annual">年报</Select.Option>
                  <Select.Option value="quarterly">季报</Select.Option>
                  <Select.Option value="semi-annual">半年报</Select.Option>
                </Select>
              </Form.Item>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={uploading}
                  icon={<UploadOutlined />}
                  className="upload-submit-btn"
                  size="large"
                  block
                >
                  {uploading ? '上传中...' : '上传并解析'}
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card
            className="upload-sidebar-card"
            title={
              <div className="upload-sidebar-title">
                <ClockCircleOutlined />
                <span>最近上传</span>
              </div>
            }
          >
            <List
              dataSource={recentUploads}
              renderItem={(item) => (
                <List.Item className="recent-upload-item">
                  <div className="recent-upload-info">
                    {getFileIcon(item.name)}
                    <div className="recent-upload-detail">
                      <div className="recent-upload-name">{item.name}</div>
                      <div className="recent-upload-meta">
                        <span>{item.size}</span>
                        <span className="recent-upload-time">{item.time}</span>
                      </div>
                    </div>
                  </div>
                  {item.status === 'success' ? (
                    <CheckCircleOutlined className="recent-upload-status success" />
                  ) : (
                    <Tag color="processing" className="recent-upload-status">解析中</Tag>
                  )}
                </List.Item>
              )}
            />
          </Card>

          <Card
            className="upload-sidebar-card"
            style={{ marginTop: 16 }}
            title={
              <div className="upload-sidebar-title">
                <SafetyCertificateOutlined />
                <span>上传须知</span>
              </div>
            }
          >
            <ul className="upload-tips">
              <li>支持 PDF、Word、Excel 格式文件</li>
              <li>单个文件大小不超过 100MB</li>
              <li>建议文件名包含公司名称和年份</li>
              <li>上传后系统将自动解析并提取关键数据</li>
              <li>解析过程可能需要 1-5 分钟，请耐心等待</li>
            </ul>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

import React, { useState, useRef, useEffect } from 'react'
import { Input, Button, List, Card, Spin, Tag } from 'antd'
import { SendOutlined, CopyOutlined, CheckOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { chatQuery } from '../api/chat'
import './ChatPage.css'

/**
 * Markdown 渲染组件 - 用于 AI 回复的富文本展示
 * 支持：标题、列表、表格、代码块、粗体、链接等
 */
function MarkdownContent({ content }) {
  return (
    <div className="markdown-body">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  )
}

/**
 * 可复制消息组件
 */
function CopyableMessage({ content }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('复制失败:', err)
    }
  }

  return (
    <div className="message-wrapper">
      <MarkdownContent content={content} />
      <Button
        type="text"
        size="small"
        icon={copied ? <CheckOutlined /> : <CopyOutlined />}
        onClick={handleCopy}
        className="copy-btn"
        title={copied ? '已复制' : '复制'}
      />
    </div>
  )
}

export default function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const messagesEndRef = useRef(null)

  // 快捷问题示例
  const quickQuestions = [
    "贵州茅台2023年营收同比增长多少？",
    "分析招商银行近三年不良率变化原因",
    "对比工行与建行的拨备覆盖率",
  ]

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async (text) => {
    const messageText = text || input
    if (!messageText.trim() || loading) return

    const userMessage = {
      role: 'user',
      content: messageText,
      timestamp: Date.now(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await chatQuery({
        message: messageText,
        conversation_id: conversationId,
        context: messages.map(({ role, content }) => ({ role, content })),
      })

      setConversationId(response.conversation_id)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.response,
          timestamp: Date.now(),
          sources: response.sources,
        },
      ])
    } catch (error) {
      console.error('发送消息失败:', error)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: '抱歉，处理您的请求时出现错误，请稍后重试。',
          timestamp: Date.now(),
          isError: true,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (!e.shiftKey && e.key === 'Enter') {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-page">
      <Card title="智能对话查询" className="chat-card">
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-empty">
              <p className="chat-welcome">欢迎使用智能财报助手！</p>
              <p className="chat-subtitle">您可以问我：</p>
              <div className="quick-questions">
                {quickQuestions.map((q, idx) => (
                  <Tag
                    key={idx}
                    className="quick-tag"
                    onClick={() => handleSend(q)}
                  >
                    {q}
                  </Tag>
                ))}
              </div>
            </div>
          )}
          <List
            dataSource={messages}
            renderItem={(item) => (
              <List.Item
                className={`chat-message ${item.role}`}
                style={{ border: 'none', padding: '12px 0' }}
              >
                <div className={`message-bubble ${item.role} ${item.isError ? 'error' : ''}`}>
                  <div className="message-content">
                    {item.role === 'assistant' ? (
                      <CopyableMessage content={item.content} />
                    ) : (
                      item.content
                    )}
                  </div>
                  {item.sources && item.sources.length > 0 && (
                    <div className="message-sources">
                      <span className="sources-label">📚 参考来源：</span>
                      {item.sources.map((source, idx) => (
                        <span key={idx} className="source-tag">
                          {source.source}
                          {source.relevance != null && (
                            <span className="source-score">
                              {(source.relevance * 100).toFixed(0)}%
                            </span>
                          )}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </List.Item>
            )}
          />
          {loading && (
            <div className="chat-loading">
              <Spin size="small" />
              <span className="loading-text">正在思考...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <div className="chat-input">
          <Input.TextArea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入您的问题，Enter 发送，Shift+Enter 换行..."
            rows={2}
            disabled={loading}
            autoSize={{ minRows: 2, maxRows: 4 }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={() => handleSend()}
            loading={loading}
            disabled={!input.trim()}
            style={{ marginTop: 8 }}
          >
            发送
          </Button>
        </div>
      </Card>
    </div>
  )
}

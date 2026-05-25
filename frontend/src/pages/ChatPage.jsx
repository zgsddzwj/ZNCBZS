import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Input, Button, List, Card, Spin, Tag, Tooltip } from 'antd'
import { SendOutlined, CopyOutlined, CheckOutlined, ClockCircleOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { chatQuery } from '../api/chat'
import './ChatPage.css'

/**
 * 打字机效果 Hook
 * @param {string} fullText - 完整文本
 * @param {number} speed - 打字速度(ms)
 * @param {boolean} enabled - 是否启用
 */
function useTypewriter(fullText, speed = 15, enabled = true) {
  const [displayText, setDisplayText] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const indexRef = useRef(0)
  const timerRef = useRef(null)

  useEffect(() => {
    if (!enabled || !fullText) {
      setDisplayText(fullText || '')
      setIsTyping(false)
      return
    }

    setIsTyping(true)
    indexRef.current = 0
    setDisplayText('')

    const typeNext = () => {
      if (indexRef.current < fullText.length) {
        // 每次渲染一个字符或一个markdown标记（优化体验）
        const nextChunk = fullText.slice(0, indexRef.current + 1)
        setDisplayText(nextChunk)
        indexRef.current += 1
        timerRef.current = setTimeout(typeNext, speed)
      } else {
        setIsTyping(false)
      }
    }

    timerRef.current = setTimeout(typeNext, speed)

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [fullText, speed, enabled])

  return { displayText, isTyping }
}

/**
 * 格式化时间显示
 */
function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()

  if (isToday) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

/**
 * Markdown 渲染组件
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
 * 可复制消息组件（带打字机效果）
 */
function CopyableMessage({ content, isStreaming }) {
  const [copied, setCopied] = useState(false)
  const { displayText, isTyping } = useTypewriter(content, 12, isStreaming)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('复制失败:', err)
    }
  }

  const textToShow = isStreaming ? displayText : content

  return (
    <div className="message-wrapper">
      <MarkdownContent content={textToShow} />
      {isTyping && <span className="typing-cursor">|</span>}
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

/**
 * 消息时间戳组件
 */
function MessageTime({ timestamp }) {
  const timeStr = formatTime(timestamp)
  if (!timeStr) return null

  return (
    <Tooltip title={new Date(timestamp).toLocaleString('zh-CN')}>
      <span className="message-time">
        <ClockCircleOutlined style={{ fontSize: 10, marginRight: 3 }} />
        {timeStr}
      </span>
    </Tooltip>
  )
}

export default function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const [streamingIndex, setStreamingIndex] = useState(null)
  const messagesEndRef = useRef(null)

  const quickQuestions = [
    "贵州茅台2023年营收同比增长多少？",
    "分析招商银行近三年不良率变化原因",
    "对比工行与建行的拨备覆盖率",
  ]

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

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

      // 先添加空消息占位，再触发打字机效果
      const assistantIndex = messages.length + 1
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.response,
          timestamp: Date.now(),
          sources: response.sources,
        },
      ])
      setStreamingIndex(assistantIndex)

      // 打字完成后清除 streaming 状态
      const typingDuration = response.response.length * 12 + 300
      setTimeout(() => {
        setStreamingIndex(null)
      }, typingDuration)

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
            renderItem={(item, index) => (
              <List.Item
                className={`chat-message ${item.role}`}
                style={{ border: 'none', padding: '12px 0' }}
              >
                <div className={`message-bubble ${item.role} ${item.isError ? 'error' : ''}`}>
                  <div className="message-header">
                    <span className="message-role-label">
                      {item.role === 'user' ? '您' : 'AI助手'}
                    </span>
                    <MessageTime timestamp={item.timestamp} />
                  </div>
                  <div className="message-content">
                    {item.role === 'assistant' ? (
                      <CopyableMessage
                        content={item.content}
                        isStreaming={index === streamingIndex}
                      />
                    ) : (
                      item.content
                    )}
                  </div>
                  {item.sources && item.sources.length > 0 && (
                    <div className="message-sources">
                      <span className="sources-label">参考来源：</span>
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
          {loading && streamingIndex === null && (
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

import React, { useState, useRef, useEffect } from 'react'
import { Input, Button, List, Card, Spin } from 'antd'
import { SendOutlined } from '@ant-design/icons'
import { chatQuery } from '../api/chat'
import './ChatPage.css'

export default function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: Date.now(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await chatQuery({
        message: input,
        conversation_id: conversationId,
        context: messages,
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
          content: '抱歉，处理您的请求时出现错误。',
          timestamp: Date.now(),
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat-page">
      <Card title="智能对话查询" className="chat-card">
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-empty">
              <p>欢迎使用智能财报助手！</p>
              <p>您可以问我：</p>
              <ul>
                <li>贵州茅台2023年营收同比增长多少？</li>
                <li>分析招商银行近三年不良率变化原因</li>
                <li>对比工行与建行的拨备覆盖率</li>
              </ul>
            </div>
          )}
          <List
            dataSource={messages}
            renderItem={(item) => (
              <List.Item
                className={`chat-message ${item.role}`}
                style={{ border: 'none', padding: '12px 0' }}
              >
                <div className={`message-bubble ${item.role}`}>
                  <div className="message-content">{item.content}</div>
                  {item.sources && item.sources.length > 0 && (
                    <div className="message-sources">
                      来源：
                      {item.sources.map((source, idx) => (
                        <span key={idx} className="source-tag">
                          {source.source}
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
              <Spin size="small" /> 正在思考...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <div className="chat-input">
          <Input.TextArea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
            placeholder="输入您的问题..."
            rows={2}
            disabled={loading}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            loading={loading}
            style={{ marginTop: 8 }}
          >
            发送
          </Button>
        </div>
      </Card>
    </div>
  )
}


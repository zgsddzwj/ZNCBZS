import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import Layout from './components/Layout'
import ChatPage from './pages/ChatPage'
import ReportPage from './pages/ReportPage'
import AnalysisPage from './pages/AnalysisPage'
import UploadPage from './pages/UploadPage'
import AgentsPage from './pages/AgentsPage'
import './App.css'

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/reports" element={<ReportPage />} />
            <Route path="/analysis" element={<AnalysisPage />} />
            <Route path="/agents" element={<AgentsPage />} />
            <Route path="/upload" element={<UploadPage />} />
          </Routes>
        </Layout>
      </Router>
    </ConfigProvider>
  )
}

export default App


import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export async function chatQuery(data) {
  const response = await api.post("/chat/query", data);
  return response.data;
}

export async function getConversationHistory(conversationId) {
  const response = await api.get(`/chat/history/${conversationId}`);
  return response.data;
}

export async function clearConversationHistory(conversationId) {
  const response = await api.delete(`/chat/history/${conversationId}`);
  return response.data;
}

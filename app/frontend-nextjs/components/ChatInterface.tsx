'use client';

import React, { useState, useRef, useEffect } from 'react';
import { User, ChatMessage as ChatMessageType } from '@/lib/types';
import { api } from '@/lib/api';
import ChatMessage from './ChatMessage';
import { Send, Loader2, LogOut } from 'lucide-react';
import { ROLE_COLORS, COLLECTION_ICONS } from '@/lib/constants';

interface ChatInterfaceProps {
  user: User;
  onLogout: () => void;
  onAdminPanel: () => void;
}

export default function ChatInterface({ user, onLogout, onAdminPanel }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [collections, setCollections] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollToBottom();
    loadCollections();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadCollections = async () => {
    try {
      const cols = await api.getCollections();
      setCollections(cols.map((c) => c.name));
    } catch (err) {
      console.error('Failed to load collections:', err);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message
    const userMessage: ChatMessageType = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await api.chat({
        user_role: user.role,
        query: input,
        user_id: user.username,
      });

      // Guard against empty/blank responses from the backend
      const answerText = response.answer?.trim()
        ? response.answer
        : "I wasn't able to generate a response for your question. Please try rephrasing or ask a different question.";

      const assistantMessage: ChatMessageType = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: answerText,
        timestamp: new Date(),
        response: { ...response, answer: answerText },
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: unknown) {
      // Extract a helpful message from the error if possible
      let errorText = 'Sorry, I encountered an error processing your query. Please try again in a moment.';
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: { error?: string; detail?: string } } };
        const serverMsg = axiosError.response?.data?.detail || axiosError.response?.data?.error;
        if (serverMsg) {
          errorText = `Sorry, something went wrong: ${serverMsg}`;
        }
      }

      const errorMessage: ChatMessageType = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: errorText,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      console.error('Chat error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">FinBot</h1>
          <p className="text-sm text-gray-600">Advanced RAG with RBAC Enforcement</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={onAdminPanel}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg font-semibold transition-colors text-sm"
          >
            Admin Panel
          </button>
          <button
            onClick={onLogout}
            className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg font-semibold transition-colors flex items-center gap-2"
          >
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </div>

      <div className="flex flex-1 gap-4 p-4 min-h-0">
        {/* Sidebar */}
        <div className="w-64 bg-white rounded-lg border border-gray-200 p-4 flex flex-col gap-4 overflow-y-auto">
          {/* User Profile */}
          <div className="border-b pb-4">
            <h3 className="text-sm font-bold text-gray-700 mb-3">Your Profile</h3>
            <div className="space-y-2">
              <div>
                <p className="text-xs text-gray-600">Name</p>
                <p className="font-semibold text-gray-900">{user.name}</p>
              </div>
              <div>
                <p className="text-xs text-gray-600">Username</p>
                <p className="font-mono text-sm text-gray-700">@{user.username}</p>
              </div>
              <div>
                <p className="text-xs text-gray-600">Department</p>
                <p className="font-semibold text-gray-900">{user.department}</p>
              </div>
              <div>
                <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${ROLE_COLORS[user.role]}`}>
                  {user.role}
                </span>
              </div>
            </div>
          </div>

          {/* Access Control */}
          <div className="border-b pb-4">
            <h3 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
              🔐 Your Access
            </h3>
            <div className="space-y-2">
              {(user.accessible_collections ?? []).map((collection) => (
                <div
                  key={collection}
                  className="flex items-center gap-2 bg-green-50 border border-green-200 rounded p-2"
                >
                  <span className="text-lg">{COLLECTION_ICONS[collection] || '📁'}</span>
                  <span className="text-sm font-semibold text-green-800">{collection}</span>
                </div>
              ))}
            </div>
            <div className="mt-3 p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-700">
              <p className="font-semibold mb-1">Restricted Collections:</p>
              <ul className="space-y-1">
                {collections
                  .filter((c) => !(user.accessible_collections ?? []).includes(c))
                  .map((c) => (
                    <li key={c} className="flex items-center gap-1.5">
                      <span className="text-xs font-bold">🚫</span>
                      {c}
                    </li>
                  ))}
              </ul>
            </div>
          </div>

          {/* System Info */}
          <div className="text-xs text-gray-600 bg-gray-50 p-3 rounded border border-gray-200">
            <p className="font-bold mb-2">System Info</p>
            <ul className="space-y-1">
              <li>
                <strong>Backend:</strong> Running
              </li>
              <li>
                <strong>Collections:</strong> {collections.length}
              </li>
              <li>
                <strong>RBAC:</strong> Enforced
              </li>
            </ul>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 bg-white rounded-lg border border-gray-200 flex flex-col min-h-0">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <div className="text-6xl mb-4">💬</div>
                  <p className="text-2xl font-bold text-gray-800 mb-2">Start a Conversation</p>
                  <p className="text-gray-600 max-w-sm">
                                Ask FinBot any questions about your company&apos;s business data. RBAC ensures you only see
                                information you&apos;re authorized to access.
                  </p>
                </div>
              </div>
            )}
            {messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                type={msg.type}
                content={msg.content}
                timestamp={msg.timestamp}
                response={msg.response}
              />
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-2xl p-4 flex items-center gap-3">
                  <Loader2 className="animate-spin text-primary-600" size={20} />
                  <span className="text-gray-600">FinBot is thinking...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-gray-200 p-4">
            <form onSubmit={handleSendMessage} className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a question about your company..."
                disabled={loading}
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="px-6 py-3 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-semibold flex items-center gap-2 transition-colors"
              >
                {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
                Send
              </button>
            </form>
            <p className="text-xs text-gray-500 mt-2">
              💡 Tip: Try asking about different collections or testing RBAC by asking about restricted content.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

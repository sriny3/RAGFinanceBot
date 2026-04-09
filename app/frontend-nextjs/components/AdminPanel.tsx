'use client';

import React, { useState, useEffect } from 'react';
import { User } from '@/lib/types';
import { api } from '@/lib/api';
import { X, Plus, Loader2, Check, AlertCircle } from 'lucide-react';
import {ROLE_COLORS } from '@/lib/constants';

interface AdminPanelProps {
  onClose: () => void;
}

export default function AdminPanel({ onClose }: AdminPanelProps) {
  const [activeTab, setActiveTab] = useState<'users' | 'management'>('users');
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [formData, setFormData] = useState({
    username: '',
    name: '',
    role: 'employee' as const,
    department: '',
  });

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const userList = await api.getUsers();
      setUsers(userList);
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to load users' });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.username || !formData.name || !formData.department) {
      setMessage({ type: 'error', text: 'All fields are required' });
      return;
    }

    try {
      setLoading(true);
      await api.adminCreateUser({
        username: formData.username,
        name: formData.name,
        role: formData.role,
        department: formData.department,
      });
      setMessage({ type: 'success', text: 'User created successfully' });
      setFormData({ username: '', name: '', role: 'employee', department: '' });
      await loadUsers();
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to create user' });
    } finally {
      setLoading(false);
    }
  };

  const handleIngest = async () => {
    try {
      setLoading(true);
      await api.adminIngest();
      setMessage({ type: 'success', text: 'Document ingestion completed successfully' });
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to trigger ingestion' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Admin Panel</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 flex">
          <button
            onClick={() => setActiveTab('users')}
            className={`flex-1 px-6 py-4 font-semibold transition-colors ${
              activeTab === 'users'
                ? 'border-b-2 border-primary-600 text-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            User Management
          </button>
          <button
            onClick={() => setActiveTab('management')}
            className={`flex-1 px-6 py-4 font-semibold transition-colors ${
              activeTab === 'management'
                ? 'border-b-2 border-primary-600 text-primary-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            System Management
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Message */}
          {message && (
            <div
              className={`mb-4 p-4 rounded-lg flex items-center gap-3 ${
                message.type === 'success'
                  ? 'bg-green-50 border border-green-200 text-green-700'
                  : 'bg-red-50 border border-red-200 text-red-700'
              }`}
            >
              {message.type === 'success' ? <Check size={20} /> : <AlertCircle size={20} />}
              {message.text}
            </div>
          )}

          {/* Users Tab */}
          {activeTab === 'users' && (
            <div className="space-y-6">
              {/* Create User Form */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">Create New User</h3>
                <form onSubmit={handleCreateUser} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Username
                      </label>
                      <input
                        type="text"
                        value={formData.username}
                        onChange={(e) =>
                          setFormData({ ...formData, username: e.target.value })
                        }
                        placeholder="e.g., user_john"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Full Name
                      </label>
                      <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        placeholder="e.g., John Doe"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Role
                      </label>
                      <select
                        value={formData.role}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            role: e.target.value as any,
                          })
                        }
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="employee">Employee</option>
                        <option value="finance">Finance</option>
                        <option value="engineering">Engineering</option>
                        <option value="marketing">Marketing</option>
                        <option value="c_level">C-Level</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Department
                      </label>
                      <input
                        type="text"
                        value={formData.department}
                        onChange={(e) =>
                          setFormData({ ...formData, department: e.target.value })
                        }
                        placeholder="e.g., Finance, Engineering"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full px-4 py-3 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white rounded-lg font-semibold flex items-center justify-center gap-2 transition-colors"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="animate-spin" size={18} />
                        Creating...
                      </>
                    ) : (
                      <>
                        <Plus size={18} />
                        Create User
                      </>
                    )}
                  </button>
                </form>
              </div>

              {/* Users List */}
              <div>
                <h3 className="text-lg font-bold text-gray-900 mb-4">Current Users</h3>
                <div className="grid gap-3 max-h-96 overflow-y-auto">
                  {users.map((user) => (
                    <div key={user.username} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="font-bold text-gray-900">{user.name}</p>
                          <p className="text-sm text-gray-600">@{user.username}</p>
                          <div className="flex items-center gap-3 mt-2">
                            <span
                              className={`px-3 py-1 rounded-full text-xs font-semibold ${ROLE_COLORS[user.role]}`}
                            >
                              {user.role}
                            </span>
                            <span className="text-xs text-gray-600">{user.department}</span>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-xs font-semibold text-gray-700 mb-1">Access:</p>
                          <div className="flex flex-wrap gap-1 justify-end">
                            {(user.accessible_collections ?? []).map((col) => (
                              <span
                                key={col}
                                className="inline-block bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs"
                              >
                                {col}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Management Tab */}
          {activeTab === 'management' && (
            <div className="space-y-6">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h3 className="text-lg font-bold text-blue-900 mb-4">Document Ingestion</h3>
                <p className="text-blue-700 mb-4">
                  Re-ingest all documents from the data folder. This will parse, chunk, embed, and store all documents in the vector database.
                </p>
                <button
                  onClick={handleIngest}
                  disabled={loading}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg font-semibold transition-colors flex items-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader2 className="animate-spin" size={18} />
                      Ingesting...
                    </>
                  ) : (
                    '📥 Re-Ingest Documents'
                  )}
                </button>
              </div>

              <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">System Configuration</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded">
                    <div>
                      <p className="font-semibold text-gray-900">RBAC Enforcement</p>
                      <p className="text-sm text-gray-600">Enabled at vector database level</p>
                    </div>
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded">
                    <div>
                      <p className="font-semibold text-gray-900">Input Guardrails</p>
                      <p className="text-sm text-gray-600">Injection, off-topic, PII detection</p>
                    </div>
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded">
                    <div>
                      <p className="font-semibold text-gray-900">Output Guardrails</p>
                      <p className="text-sm text-gray-600">Grounding, citations, leakage detection</p>
                    </div>
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded">
                    <div>
                      <p className="font-semibold text-gray-900">Semantic Routing</p>
                      <p className="text-sm text-gray-600">5 intent-based routes configured</p>
                    </div>
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded">
                    <div>
                      <p className="font-semibold text-gray-900">LLM (Groq)</p>
                      <p className="text-sm text-gray-600">
                        Inference via backend <code className="text-xs bg-gray-100 px-1 rounded">GROQ_API_KEY</code> — not stored in the browser
                      </p>
                    </div>
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  </div>
                </div>
              </div>

              <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
                <h3 className="text-lg font-bold text-purple-900 mb-4">Collections</h3>
                <div className="space-y-3">
                  {['general', 'finance', 'engineering', 'marketing', 'hr'].map((collection) => (
                    <div key={collection} className="flex items-center justify-between p-3 bg-white border border-purple-100 rounded">
                      <span className="font-semibold text-gray-900 capitalize">{collection}</span>
                      <span className="text-sm text-gray-600">✓ Configured</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

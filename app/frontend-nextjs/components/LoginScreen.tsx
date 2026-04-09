'use client';

import React, { useState, useEffect } from 'react';
import { User } from '@/lib/types';
import { api } from '@/lib/api';
import { DEMO_USERS, ROLE_COLORS } from '@/lib/constants';
import { AlertCircle, Loader2 } from 'lucide-react';

interface LoginScreenProps {
  onLogin: (user: User) => void;
}

export default function LoginScreen({ onLogin }: LoginScreenProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [systemHealth, setSystemHealth] = useState<boolean | null>(null);
  const [collectionsReady, setCollectionsReady] = useState<boolean>(false);

  useEffect(() => {
    checkSystemHealth();
  }, []);

  const checkSystemHealth = async () => {
    try {
      const health = await api.health();
      const isHealthy = health.status === 'healthy';
      setSystemHealth(isHealthy);
      setCollectionsReady(isHealthy && health.collections_available);
      if (isHealthy && !health.collections_available) {
        setError('Backend is running but no documents have been ingested yet. Use POST /api/admin/ingest to load data.');
      }
    } catch {
      setSystemHealth(false);
      setError('Backend not responding. Ensure backend is running on http://localhost:8000');
    }
  };

  const handleLogin = async (username: string) => {
    try {
      setLoading(true);
      setError(null);
      const user = await api.getUser(username);
      onLogin(user);
    } catch (err) {
      setError(`Failed to login. Please ensure backend is running.`);
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-600 via-secondary-600 to-primary-800 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-block bg-white/10 backdrop-blur-md rounded-2xl p-6 mb-6">
            <h1 className="text-5xl font-bold text-white mb-2">FinBot</h1>
            <p className="text-white/80 text-lg">Advanced RAG System with RBAC</p>
          </div>

          {/* System Status */}
          {systemHealth === false && (
            <div className="bg-red-500/10 border border-red-500 rounded-lg p-4 mb-6 flex items-start gap-3">
              <AlertCircle className="text-red-500 flex-shrink-0 mt-0.5" size={20} />
              <div className="text-left">
                <p className="text-red-700 font-semibold">Backend Connection Error</p>
                <p className="text-red-600 text-sm">
                  {error || 'Unable to connect to backend. Please ensure the Python backend is running on http://localhost:8000'}
                </p>
              </div>
            </div>
          )}

          {systemHealth === true && !collectionsReady && (
            <div className="bg-yellow-500/10 border border-yellow-500 rounded-lg p-4 mb-6 flex items-start gap-3">
              <AlertCircle className="text-yellow-500 flex-shrink-0 mt-0.5" size={20} />
              <div className="text-left">
                <p className="text-yellow-700 font-semibold">⚠ Backend Online — No Documents Ingested</p>
                <p className="text-yellow-600 text-sm">
                  {error || 'Run document ingestion first: POST /api/admin/ingest'}
                </p>
              </div>
            </div>
          )}

          {systemHealth === true && collectionsReady && (
            <div className="bg-green-500/20 border border-green-400 rounded-lg p-3 mb-6">
              <p className="text-green-300 text-sm font-medium tracking-wide">✓ System Online — All Collections Available</p>
            </div>
          )}
        </div>

        {/* Login Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          {DEMO_USERS.map((demoUser) => (
            <button
              key={demoUser.username}
              onClick={() => handleLogin(demoUser.username)}
              disabled={loading || systemHealth === false || systemHealth === null}
              className={`group relative overflow-hidden rounded-xl p-6 transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed ${
                demoUser.color
              } border-2 hover:shadow-lg`}
            >
              <div className="absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-10 transition-opacity" />
              <div className="relative">
                <div className="text-4xl mb-3">{demoUser.icon}</div>
                <div className="text-left">
                  <p className="font-bold text-lg">{demoUser.name}</p>
                  <p className="text-sm opacity-75 mb-2">@{demoUser.username}</p>
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold ${ROLE_COLORS[demoUser.role]}`}
                    >
                      {demoUser.role}
                    </span>
                  </div>
                </div>
              </div>

              {loading && (
                <div className="absolute inset-0 bg-black/20 flex items-center justify-center rounded-xl">
                  <Loader2 className="animate-spin text-white" size={24} />
                </div>
              )}
            </button>
          ))}
        </div>

        {/* Info Cards */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <span className="text-xl">ℹ️</span> About This Demo
          </h3>
          <div className="text-white/90 space-y-3 text-sm">
            <p>
              <strong>RBAC Demonstration:</strong> Each user has different access levels. Try logging in as different roles and querying restricted content.
            </p>
            <p>
              <strong>Test Queries:</strong>
              <br />
                              - General: &quot;What are our company policies?&quot;
              <br />
                              - Finance: &quot;What was Q3 revenue?&quot; (finance users only)
              <br />
                              - Engineering: &quot;Tell me about system architecture&quot; (engineering users only)
                              - RBAC Test: Ask finance questions as a marketing user -&gt; Access denied
            </p>
            <p>
              <strong>Guardrails:</strong> Try prompt injection or off-topic queries to see guardrail warnings in real-time.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

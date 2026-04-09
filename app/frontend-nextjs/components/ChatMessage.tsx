'use client';

import React from 'react';
import { RAGResponse } from '@/lib/types';
import { ExternalLink, FileText, MapPin } from 'lucide-react';
import RBACBlock from './RBACBlock';
import GuardrailBanner from './GuardrailBanner';

interface ChatMessageProps {
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  response?: RAGResponse;
}

export default function ChatMessage({ type, content, timestamp, response }: ChatMessageProps) {
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  if (type === 'system') {
    return (
      <div className="flex justify-center my-4">
        <div className="bg-gray-100 text-gray-700 px-4 py-2 rounded-full text-sm">
          {content}
        </div>
      </div>
    );
  }

  const isUser = type === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6 animate-slideIn`}>
      <div className={`max-w-2xl ${isUser ? 'mr-4' : 'ml-4'}`}>
        {/* User Message */}
        {isUser && (
          <div>
            <div className="bg-primary-600 text-white rounded-2xl rounded-tr-sm px-6 py-4 flex-1">
              <p className="break-words">{content}</p>
            </div>
            <p className="text-xs text-gray-500 mt-1 text-right">{formatTime(timestamp)}</p>
          </div>
        )}

        {/* Assistant Message */}
        {!isUser && response && (
          <div>
            {/* RBAC Denial Block */}
            {response.rbac_denied && (
              <>
                <RBACBlock
                  message="Your query targeted a collection you don't have access to."
                  denialReason={response.rbac_denial_reason}
                />
              </>
            )}

            {/* Guardrail Warnings */}
            {response.guardrail_flags && response.guardrail_flags.length > 0 && (
              <div className="mb-4">
                <GuardrailBanner flags={response.guardrail_flags} />
              </div>
            )}

            {/* Main Answer */}
            {!response.rbac_denied && (
              <div>
                <div className="bg-gray-50 border border-gray-200 rounded-2xl rounded-tl-sm px-6 py-4 mb-4">
                  <p className="text-gray-900 break-words leading-relaxed">{response.answer}</p>
                </div>

                {/* Metadata Section */}
                <div className="space-y-3 text-sm">
                  {/* Route Information */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start gap-3">
                    <div className="flex-shrink-0 text-blue-600 font-bold">🔄</div>
                    <div className="flex-1">
                      <p className="text-blue-900 font-semibold">Semantic Route</p>
                      <p className="text-blue-700">
                        {(response.route ?? '')
                          .replace(/_/g, ' ')
                          .replace(/route/i, '')
                          .trim()}
                      </p>
                    </div>
                  </div>

                  {/* User Role & Access */}
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 flex items-start gap-3">
                    <div className="flex-shrink-0 text-purple-600 font-bold">👤</div>
                    <div className="flex-1">
                      <p className="text-purple-900 font-semibold">Your Access</p>
                      <div className="flex flex-wrap gap-2 mt-1">
                        <span className="inline-block bg-purple-200 text-purple-800 px-2 py-1 rounded text-xs font-semibold">
                          {response.user_role}
                        </span>
                        {(response.accessible_collections ?? []).map((collection) => (
                          <span key={collection} className="inline-block bg-purple-100 text-purple-700 px-2 py-1 rounded text-xs">
                            {collection}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Sources */}
                  {(response.sources ?? []).length > 0 && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                      <p className="text-green-900 font-semibold mb-3 flex items-center gap-2">
                        <FileText size={16} /> Sources ({(response.sources ?? []).length})
                      </p>
                      <div className="space-y-2">
                        {(response.sources ?? []).map((source, idx) => (
                          <div key={idx} className="bg-white border border-green-100 rounded p-2 text-xs">
                            <div className="flex items-start gap-2">
                              <ExternalLink size={14} className="text-green-600 flex-shrink-0 mt-0.5" />
                              <div>
                                <p className="text-gray-800 font-semibold">{source.document}</p>
                                <div className="flex gap-4 text-gray-600 mt-1">
                                  {source.page_number && (
                                    <span className="flex items-center gap-1">
                                      <MapPin size={12} />
                                      Page {source.page_number}
                                    </span>
                                  )}
                                  {source.section_title && (
                                    <span className="italic text-gray-500">{source.section_title}</span>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            <p className="text-xs text-gray-500 mt-3">{formatTime(timestamp)}</p>
          </div>
        )}
      </div>
    </div>
  );
}

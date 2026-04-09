'use client';

import React from 'react';
import { GuardrailFlag } from '@/lib/types';
import { normalizeGuardrailFlags } from '@/lib/normalize';
import { AlertCircle, AlertTriangle, X } from 'lucide-react';
import { GUARDRAIL_COLORS } from '@/lib/constants';

interface GuardrailBannerProps {
  flags: GuardrailFlag[] | string[] | undefined;
  onDismiss?: () => void;
}

export default function GuardrailBanner({ flags, onDismiss }: GuardrailBannerProps) {
  const normalized = normalizeGuardrailFlags(flags);
  if (normalized.length === 0) return null;

  return (
    <div className="space-y-3">
      {normalized.map((flag, idx) => (
        <div
          key={idx}
          className={`border-l-4 flex items-start gap-3 p-4 rounded-lg ${GUARDRAIL_COLORS[flag.severity]}`}
        >
          {flag.severity === 'error' ? (
            <AlertTriangle size={20} className="flex-shrink-0 mt-0.5" />
          ) : (
            <AlertCircle size={20} className="flex-shrink-0 mt-0.5" />
          )}
          <div className="flex-1">
            <p className="font-semibold capitalize mb-1">{flag.type.replace(/_/g, ' ')}</p>
            <p className="text-sm opacity-90">{flag.message}</p>
          </div>
          {onDismiss && (
            <button onClick={onDismiss} className="flex-shrink-0 hover:opacity-70">
              <X size={18} />
            </button>
          )}
        </div>
      ))}
    </div>
  );
}

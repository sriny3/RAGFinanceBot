'use client';

import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface RBACBlockProps {
  message?: string;
  denialReason?: string;
}

export default function RBACBlock({ message, denialReason }: RBACBlockProps) {
  return (
    <div className="bg-red-50 border-2 border-red-300 rounded-lg p-6 my-4 flex items-start gap-4">
      <div className="flex-shrink-0">
        <AlertTriangle className="text-red-600" size={28} />
      </div>
      <div className="flex-1">
        <h3 className="text-red-800 font-bold text-lg mb-2">Access Denied</h3>
        <p className="text-red-700 mb-3">
          {message || 'You do not have permission to access this information based on your role.'}
        </p>
        {denialReason && (
          <div className="bg-red-100 rounded p-3 border border-red-200">
            <p className="text-red-700 text-sm">
              <strong>Reason:</strong> {denialReason}
            </p>
          </div>
        )}
        <p className="text-red-600 text-sm mt-3">
          Please contact your administrator if you believe this is an error.
        </p>
      </div>
    </div>
  );
}

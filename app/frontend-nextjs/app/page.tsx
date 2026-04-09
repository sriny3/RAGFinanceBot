'use client';

import React, { useState } from 'react';
import { User } from '@/lib/types';
import LoginScreen from '@/components/LoginScreen';
import ChatInterface from '@/components/ChatInterface';
import AdminPanel from '@/components/AdminPanel';

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [showAdmin, setShowAdmin] = useState(false);

  if (showAdmin) {
    return <AdminPanel onClose={() => setShowAdmin(false)} />;
  }

  if (!user) {
    return <LoginScreen onLogin={setUser} />;
  }

  return (
    <ChatInterface
      user={user}
      onLogout={() => setUser(null)}
      onAdminPanel={() => setShowAdmin(true)}
    />
  );
}

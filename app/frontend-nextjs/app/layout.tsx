import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'FinBot - Advanced RAG with RBAC',
  description: 'FinBot is a production-grade Retrieval-Augmented Generation system with role-based access control, hierarchical chunking, and enterprise guardrails.',
  keywords: ['RAG', 'LLM', 'RBAC', 'Information Retrieval', 'Security'],
  authors: [{ name: 'Codebasics AI Bootcamp' }],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

export type UserRole = 'employee' | 'finance' | 'engineering' | 'marketing' | 'c_level';

export interface User {
  username: string;
  name: string;
  role: UserRole;
  department: string;
  accessible_collections: string[];
}

export interface Chunk {
  id: string;
  text: string;
  source_document: string;
  collection: string;
  access_roles: UserRole[];
  section_title?: string;
  chunk_type: 'text' | 'table' | 'code' | 'heading';
  parent_chunk_id?: string;
  parent_summary?: string;
  page_number?: number;
}

export interface RetrievalResult {
  chunks: Chunk[];
  rbac_passed: boolean;
}

export interface GuardrailFlag {
  type: string;
  message: string;
  severity: 'warning' | 'error';
}

export interface RAGResponse {
  answer: string;
  sources: Array<{
    document: string;
    page_number?: number;
    section_title?: string;
  }>;
  route: string;
  user_role: UserRole;
  accessible_collections: string[];
  guardrail_flags: GuardrailFlag[];
  guardrail_warnings: string[];
  rbac_denied: boolean;
  rbac_denial_reason?: string;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  response?: RAGResponse;
}

export interface ChatRequest {
  user_role: UserRole;
  query: string;
  user_id: string;
}

export interface CollectionInfo {
  name: string;
  description: string;
  accessible_roles: UserRole[];
  points_count?: number;
  vectors_count?: number;
}

export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy';
  collections_available: boolean;
  collections: string[];
}

export interface AdminCreateUserRequest {
  username: string;
  name: string;
  role: UserRole;
  department: string;
}

export interface AdminUser extends User {
  created_at?: string;
  created_by?: string;
}

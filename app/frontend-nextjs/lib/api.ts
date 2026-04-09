import axios, { AxiosInstance } from 'axios';
import { ChatRequest, RAGResponse, User, CollectionInfo, HealthCheckResponse } from './types';
import { normalizeRAGResponse, normalizeUser } from './normalize';

class FinBotAPI {
  private client: AxiosInstance;

  constructor(baseURL: string = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // Chat API
  async chat(request: ChatRequest): Promise<RAGResponse> {
    const response = await this.client.post('/api/chat', request);
    return normalizeRAGResponse(response.data);
  }

  // Users API
  async getUsers(): Promise<User[]> {
    const response = await this.client.get('/api/users');
    const data = response.data;
    if (!Array.isArray(data)) return [];
    return data.map((u) => normalizeUser(u));
  }

  async getUser(username: string): Promise<User> {
    const response = await this.client.get(`/api/users/${username}`);
    return normalizeUser(response.data);
  }

  // Collections API
  async getCollections(): Promise<CollectionInfo[]> {
    const response = await this.client.get('/api/collections');
    const data = response.data;
    return Array.isArray(data) ? data : [];
  }

  async getCollection(name: string): Promise<CollectionInfo> {
    const response = await this.client.get<CollectionInfo>(`/api/collections/${name}`);
    return response.data;
  }

  // Health API
  async health(): Promise<HealthCheckResponse> {
    const response = await this.client.get<HealthCheckResponse>('/api/health');
    return response.data;
  }

  // Admin API
  async adminCreateUser(data: { username: string; name: string; role: string; department: string }) {
    const response = await this.client.post('/api/admin/users', data);
    return response.data;
  }

  async adminIngest() {
    const response = await this.client.post('/api/admin/ingest');
    return response.data;
  }

  // System Info
  async getSystemInfo() {
    const response = await this.client.get('/api/info');
    return response.data;
  }
}

export const api = new FinBotAPI();

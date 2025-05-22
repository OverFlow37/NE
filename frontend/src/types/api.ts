import { Agent, BlogPost, DownloadOption } from './models';

// API 응답 타입
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

// 페이지네이션 응답 타입
export interface PaginatedResponse<T> {
  content: T[];
  page: number;
  size: number;
  totalElements: number;
  totalPages: number;
}

// API 엔드포인트 타입
export interface ApiEndpoints {
  getAgents: () => Promise<ApiResponse<Agent[]>>;
  getAgent: (id: string) => Promise<ApiResponse<Agent>>;
  getBlogPosts: (page?: number, size?: number) => Promise<ApiResponse<PaginatedResponse<BlogPost>>>;
  getBlogPost: (id: string) => Promise<ApiResponse<BlogPost>>;
  getBlogPostBySlug: (slug: string) => Promise<ApiResponse<BlogPost>>;
  getDownloadOptions: () => Promise<ApiResponse<DownloadOption[]>>;
}

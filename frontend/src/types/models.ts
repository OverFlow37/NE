// 에이전트 타입
export interface Agent {
  id: string;
  name: string;
  description: string;
  role: string;
  personality: string;
  interests: string;
  behavior: string;
  imageUrl: string;
  backstory: string;
  behaviorPatterns: string;
  relationships: string;
  behaviorExamples?: string;
  active: boolean;
}

// 블로그 포스트 타입
export interface BlogPost {
  id: string;
  title: string;
  content: string;
  summary: string;
  slug: string;
  featuredImage: string;
  authorName: string;
  tags: string[];
  publishedAt: string;
}

// 게임 특징 타입
export interface GameFeature {
  id: string;
  title: string;
  description: string;
  iconName: string;
}

// 다운로드 옵션 타입
export interface DownloadOption {
  id: string;
  platform: 'windows' | 'macos' | 'linux';
  version: string;
  fileUrl: string;
  fileSize: string;
}

// 시스템 요구사항 타입
export interface SystemRequirement {
  type: 'minimum' | 'recommended';
  os: string;
  processor: string;
  memory: string;
  graphics: string;
  storage: string;
  additionalNotes?: string;
}

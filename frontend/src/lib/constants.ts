// 메타 데이터
export const SITE_NAME = 'Project New Eden';
export const SITE_DESCRIPTION =
  '로컬 LLM(Ollama의 Gemma3)을 사용하여 유니티 게임 내 에이전트들에게 지능적이고 다양한 행동을 부여하는 AI 시스템';

// 소셜 미디어 링크
export const SOCIAL_LINKS = {
  discord: 'https://discord.gg/',
  twitter: 'https://twitter.com/',
  github: 'https://github.com/',
};

// 네비게이션 링크
export const NAV_LINKS = [
  { href: '/game', label: '게임 소개' },
  { href: '/agents', label: '에이전트' },
  { href: '/technology', label: '기술 구조' },
  { href: '/download', label: '다운로드' },
  { href: '/blog', label: '개발자 노트' },
];

// 빌드 및 버전 정보
export const CURRENT_VERSION = '0.9.5';
export const BUILD_DATE = '2025-05-21';

// 시스템 요구사항
export const SYSTEM_REQUIREMENTS = {
  minimum: {
    os: 'Windows 10',
    processor: 'Intel i5-9400 / AMD Ryzen 5 3600',
    memory: '16GB RAM',
    graphics: 'NVIDIA GTX 1060 / AMD RX 580',
    storage: '8GB',
    additionalNotes: 'Ollama 설치 필요',
  },
  recommended: {
    os: 'Windows 11',
    processor: 'Intel i7-10700K / AMD Ryzen 7 5800X',
    memory: '32GB RAM',
    graphics: 'NVIDIA RTX 3060 / AMD RX 6700 XT',
    storage: 'SSD 15GB 이상',
    additionalNotes: 'Ollama 및 최신 GPU 드라이버 설치',
  },
};

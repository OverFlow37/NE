export * from './models';
export * from './api';

// 기타 공통 타입
export type ReactChildren = {
  children: React.ReactNode;
};

export interface Theme {
  isDark: boolean;
  toggleTheme: () => void;
}

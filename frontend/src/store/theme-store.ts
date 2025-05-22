import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Theme } from '@/types';

export const useThemeStore = create<Theme>()(
  persist(
    (set) => ({
      isDark: false,
      toggleTheme: () => set((state) => ({ isDark: !state.isDark })),
    }),
    {
      name: 'theme-storage',
    }
  )
);

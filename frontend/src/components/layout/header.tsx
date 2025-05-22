'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useScrollPosition } from '@/hooks/use-scroll-position';
import { useMediaQuery } from '@/hooks/use-media-query';
import { FaDiscord, FaTwitter, FaGithub, FaBars, FaTimes } from 'react-icons/fa';

export default function Header() {
  const pathname = usePathname();
  const scrollPosition = useScrollPosition();
  const isMobile = useMediaQuery('(max-width: 768px)');
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  // 모바일 메뉴가 열렸을 때 스크롤 방지
  useEffect(() => {
    if (isMenuOpen && isMobile) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isMenuOpen, isMobile]);

  // 스크롤 위치에 따라 헤더 스타일 변경
  const isScrolled = scrollPosition > 50;

  const navLinks = [
    { href: '/game', label: '게임 소개' },
    { href: '/agents', label: '에이전트' },
    { href: '/technology', label: '기술 구조' },
    { href: '/download', label: '다운로드' },
    { href: '/blog', label: '개발자 노트' },
  ];

  return (
    <header
      className={`fixed w-full z-50 transition-all duration-300 ${
        isScrolled
          ? 'bg-white bg-opacity-90 backdrop-blur-sm shadow-md py-2'
          : 'bg-transparent py-4'
      }`}
    >
      <div className="container mx-auto px-4 flex justify-between items-center">
        <div className="flex items-center">
          <Link href="/" className="text-2xl font-bold text-gray-900">
            Project New Eden
          </Link>
        </div>

        {/* 데스크톱 네비게이션 */}
        <nav className="hidden lg:block lg:flex">
          <ul className="flex space-x-8">
            {navLinks.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className={`hover:text-primary-600 transition-colors ${
                    pathname === link.href ? 'text-primary-600 font-medium' : 'text-gray-700'
                  }`}
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <div className="flex items-center space-x-4">
          <a
            href="https://discord.gg/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xl text-gray-700 hover:text-primary-600 transition-colors"
            aria-label="Discord"
          >
            <FaDiscord />
          </a>
          <a
            href="https://twitter.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xl text-gray-700 hover:text-primary-600 transition-colors"
            aria-label="Twitter"
          >
            <FaTwitter />
          </a>
          <a
            href="https://github.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xl text-gray-700 hover:text-primary-600 transition-colors"
            aria-label="GitHub"
          >
            <FaGithub />
          </a>

          {/* 모바일 메뉴 버튼 */}
          <button
            className="lg:hidden text-2xl text-gray-700"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-label="Toggle menu"
          >
            {isMenuOpen ? <FaTimes /> : <FaBars />}
          </button>
        </div>
      </div>

      {/* 모바일 메뉴 */}
      {isMenuOpen && isMobile && (
        <div className="fixed inset-0 bg-white z-40 pt-20">
          <nav className="container mx-auto px-4">
            <ul className="flex flex-col space-y-6 py-8">
              {navLinks.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className={`text-xl ${
                      pathname === link.href ? 'text-primary-600 font-medium' : 'text-gray-700'
                    }`}
                    onClick={() => setIsMenuOpen(false)}
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      )}
    </header>
  );
}

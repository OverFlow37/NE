import Link from 'next/link';
import { FaDiscord, FaTwitter, FaGithub } from 'react-icons/fa';

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-white py-12">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <h3 className="text-xl font-bold mb-4">Project New Eden</h3>
            <p className="text-gray-400 mb-4">
              로컬 LLM(Ollama의 Gemma3)을 활용하여 유니티 게임 내 에이전트들에게 지능적이고 다양한
              행동을 부여하는 AI 시스템
            </p>
            <div className="flex space-x-4">
              <a
                href="https://discord.gg/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-white transition-colors"
                aria-label="Discord"
              >
                <FaDiscord size={24} />
              </a>

              <a
                href="https://twitter.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-white transition-colors"
                aria-label="Twitter"
              >
                <FaTwitter size={24} />
              </a>

              <a
                href="https://github.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-white transition-colors"
                aria-label="GitHub"
              >
                <FaGithub size={24} />
              </a>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-4">정보</h3>
            <ul className="space-y-2">
              <li>
                <Link href="/game" className="text-gray-400 hover:text-white transition-colors">
                  게임 소개
                </Link>
              </li>
              <li>
                <Link
                  href="/technology"
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  기술 구조
                </Link>
              </li>
              <li>
                <Link href="/agents" className="text-gray-400 hover:text-white transition-colors">
                  에이전트
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-4">다운로드</h3>
            <ul className="space-y-2">
              <li>
                <Link href="/download" className="text-gray-400 hover:text-white transition-colors">
                  게임 다운로드
                </Link>
              </li>
              <li>
                <a
                  href="https://ollama.ai/download"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  Ollama 다운로드
                </a>
              </li>
              {/* <li>
                <Link
                  href="/download/archive"
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  이전 버전
                </Link>
              </li> */}
            </ul>
          </div>

          {/* <div>
            <h3 className="text-lg font-semibold mb-4">지원</h3>
            <ul className="space-y-2">
              <li>
                <Link href="/faq" className="text-gray-400 hover:text-white transition-colors">
                  자주 묻는 질문
                </Link>
              </li>
              <li>
                <Link href="/privacy" className="text-gray-400 hover:text-white transition-colors">
                  개인정보처리방침
                </Link>
              </li>
              <li>
                <Link href="/terms" className="text-gray-400 hover:text-white transition-colors">
                  이용약관
                </Link>
              </li>
            </ul>
          </div> */}
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
          <p>&copy; 2025 OH MAI GOD. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}

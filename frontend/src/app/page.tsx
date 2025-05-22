import Image from 'next/image';
import Link from 'next/link';
import { FaDownload, FaInfoCircle, FaGlobe, FaDatabase, FaBrain } from 'react-icons/fa';
import { gameFeatures } from '@/data/game-features';
import { blogPosts } from '@/data/blog-posts';
import { formatDate } from '@/lib/utils';

export default function Home() {
  // 최신 블로그 포스트 3개만 표시
  const latestPosts = [...blogPosts]
    .sort((a, b) => new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime())
    .slice(0, 3);

  return (
    <div>
      {/* 히어로 섹션 */}
      <section className="bg-gradient-to-r from-blue-900 to-purple-900 text-white py-20">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row ml-20 items-center">
            <div className="md:w-1/2 mb-10 md:mb-0">
              <h1 className="text-4xl md:text-5xl font-bold mb-4">Project New Eden</h1>
              <p className="text-xl mb-8">
                로컬 LLM을 활용한 에이전트 인공지능 시스템으로 <br /> 자연스럽고 지능적인 가상
                세계를 경험하세요
              </p>

              <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
                <Link
                  href="/download"
                  className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg flex items-center justify-center"
                >
                  <FaDownload className="mr-2" /> 다운로드
                </Link>
                <Link
                  href="/game"
                  className="bg-transparent border-2 border-white hover:bg-white hover:text-blue-900 text-white font-bold py-3 px-6 rounded-lg flex items-center justify-center"
                >
                  <FaInfoCircle className="mr-2" /> 더 알아보기
                </Link>
              </div>
            </div>
            <div className="md:w-1/2">
              <div className="relative w-full h-[300px] md:h-[400px] rounded-lg overflow-hidden">
                <Image
                  src="/images/hero-image.jpg"
                  alt="AI Agent Simulation"
                  fill
                  style={{ objectFit: 'contain' }}
                  priority
                  sizes="(max-width: 768px) 100vw, 50vw"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 특징 섹션 */}
      <section className="py-16 bg-gray-100">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">주요 특징</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {gameFeatures.slice(0, 3).map((feature) => (
              <div key={feature.id} className="bg-white rounded-lg shadow-md p-6">
                <div className="bg-blue-100 text-blue-800 p-3 rounded-full w-14 h-14 flex items-center justify-center mb-4">
                  {feature.iconName === 'Brain' && <FaBrain className="h-8 w-8" />}
                  {feature.iconName === 'Users' && <FaGlobe className="h-8 w-8" />}
                  {feature.iconName === 'Database' && <FaDatabase className="h-8 w-8" />}
                </div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 최신 업데이트 섹션 */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">최신 소식</h2>
          <div className="max-w-3xl mx-auto">
            {latestPosts.map((post) => (
              <div key={post.id} className="border-l-4 border-blue-500 pl-4 mb-8">
                <h3 className="text-xl font-semibold mb-2">{post.title}</h3>
                <p className="text-gray-600 mb-2">{formatDate(post.publishedAt)}</p>
                <p className="mb-2">{post.summary}</p>
                <Link href={`/blog/${post.slug}`} className="text-blue-600 hover:text-blue-800">
                  자세히 보기 →
                </Link>
              </div>
            ))}

            <div className="text-center mt-8">
              <Link href="/blog" className="text-blue-600 hover:text-blue-800 font-semibold">
                모든 소식 보기 →
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* 커뮤니티 섹션 */}
      <section className="py-16 bg-gray-800 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-6">커뮤니티에 참여하세요</h2>
          <p className="text-xl mb-8 max-w-2xl mx-auto">
            디스코드 서버에 참여하여 다른 플레이어들과 경험을 공유하고, <br /> 개발 소식을 가장 먼저
            접하세요.
          </p>
          <a
            href="https://discord.gg/"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-8 rounded-lg"
          >
            디스코드 참여하기
          </a>
        </div>
      </section>
    </div>
  );
}

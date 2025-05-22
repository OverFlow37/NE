import { Metadata } from 'next';
import Image from 'next/image';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';
import { blogPosts } from '@/data/blog-posts';
import { formatDate } from '@/lib/utils';
import { FaCalendar, FaUser, FaTags, FaArrowLeft } from 'react-icons/fa';
import { notFound } from 'next/navigation';

// 동적 메타데이터 생성
export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const resolvedParams = await params;
  const post = blogPosts.find((post) => post.slug === resolvedParams.slug);

  if (!post) {
    return {
      title: '포스트를 찾을 수 없음',
      description: '요청하신 블로그 포스트를 찾을 수 없습니다.',
    };
  }

  return {
    title: post.title,
    description: post.summary,
  };
}

// 정적 생성을 위해 가능한 모든 슬러그 생성
export async function generateStaticParams(): Promise<{ slug: string }[]> {
  return blogPosts.map((post) => ({
    slug: post.slug,
  }));
}

export default async function BlogPostPage({ params }: { params: Promise<{ slug: string }> }) {
  const resolvedParams = await params;
  const post = blogPosts.find((post) => post.slug === resolvedParams.slug);

  if (!post) {
    notFound();
    return null;
  }

  return (
    <div>
      {/* 블로그 포스트 헤더 */}
      <section className="bg-gradient-to-r from-blue-900 to-purple-900 text-white py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <Link
              href="/blog"
              className="inline-flex items-center text-blue-300 hover:text-white mb-6"
            >
              <FaArrowLeft className="mr-2" /> 모든 게시물로 돌아가기
            </Link>
            <h1 className="text-3xl md:text-5xl font-bold mb-4">{post.title}</h1>
            <div className="flex flex-wrap items-center text-sm md:text-base gap-4 md:gap-8">
              <div className="flex items-center">
                <FaUser className="mr-2" /> {post.authorName}
              </div>
              <div className="flex items-center">
                <FaCalendar className="mr-2" /> {formatDate(post.publishedAt)}
              </div>
              <div className="flex items-center">
                <FaTags className="mr-2" />
                {post.tags.map((tag, index) => (
                  <span key={tag}>
                    #{tag}
                    {index < post.tags.length - 1 ? ', ' : ''}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 블로그 포스트 특성 이미지 */}
      <div className="w-full relative h-64 md:h-96">
        <Image
          src={post.featuredImage}
          alt={post.title}
          fill
          style={{ objectFit: 'cover' }}
          priority
          sizes="100vw"
        />
      </div>

      {/* 블로그 포스트 내용 */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <div className="prose lg:prose-xl mx-auto">
              <ReactMarkdown>{post.content}</ReactMarkdown>
            </div>

            {/* 공유 버튼 */}
            <div className="mt-12 pt-6 border-t border-gray-200">
              <h3 className="text-lg font-semibold mb-4">이 글 공유하기</h3>
              <div className="flex space-x-4">
                <button className="bg-blue-600 text-white p-2 rounded-full hover:bg-blue-700">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="20"
                    height="20"
                    fill="currentColor"
                    viewBox="0 0 16 16"
                  >
                    <path d="M5.026 15c6.038 0 9.341-5.003 9.341-9.334 0-.14 0-.282-.006-.422A6.685 6.685 0 0 0 16 3.542a6.658 6.658 0 0 1-1.889.518 3.301 3.301 0 0 0 1.447-1.817 6.533 6.533 0 0 1-2.087.793A3.286 3.286 0 0 0 7.875 6.03a9.325 9.325 0 0 1-6.767-3.429 3.289 3.289 0 0 0 1.018 4.382A3.323 3.323 0 0 1 .64 6.575v.045a3.288 3.288 0 0 0 2.632 3.218 3.203 3.203 0 0 1-.865.115 3.23 3.23 0 0 1-.614-.057 3.283 3.283 0 0 0 3.067 2.277A6.588 6.588 0 0 1 .78 13.58a6.32 6.32 0 0 1-.78-.045A9.344 9.344 0 0 0 5.026 15z" />
                  </svg>
                </button>
                <button className="bg-blue-800 text-white p-2 rounded-full hover:bg-blue-900">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="20"
                    height="20"
                    fill="currentColor"
                    viewBox="0 0 16 16"
                  >
                    <path d="M16 8.049c0-4.446-3.582-8.05-8-8.05C3.58 0-.002 3.603-.002 8.05c0 4.017 2.926 7.347 6.75 7.951v-5.625h-2.03V8.05H6.75V6.275c0-2.017 1.195-3.131 3.022-3.131.876 0 1.791.157 1.791.157v1.98h-1.009c-.993 0-1.303.621-1.303 1.258v1.51h2.218l-.354 2.326H9.25V16c3.824-.604 6.75-3.934 6.75-7.951z" />
                  </svg>
                </button>
                <button className="bg-green-600 text-white p-2 rounded-full hover:bg-green-700">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="20"
                    height="20"
                    fill="currentColor"
                    viewBox="0 0 16 16"
                  >
                    <path d="M13.601 2.326A7.854 7.854 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.926c0 1.399.366 2.76 1.057 3.965L0 16l4.204-1.102a7.933 7.933 0 0 0 3.79.965h.004c4.368 0 7.926-3.558 7.93-7.93A7.898 7.898 0 0 0 13.6 2.326zM7.994 14.521a6.573 6.573 0 0 1-3.356-.92l-.24-.144-2.494.654.666-2.433-.156-.251a6.56 6.56 0 0 1-1.007-3.505c0-3.626 2.957-6.584 6.591-6.584a6.56 6.56 0 0 1 4.66 1.931 6.557 6.557 0 0 1 1.928 4.66c-.004 3.639-2.961 6.592-6.592 6.592zm3.615-4.934c-.197-.099-1.17-.578-1.353-.646-.182-.065-.315-.099-.445.099-.133.197-.513.646-.627.775-.114.133-.232.148-.43.05-.197-.1-.836-.308-1.592-.985-.59-.525-.985-1.175-1.103-1.372-.114-.198-.011-.304.088-.403.087-.088.197-.232.296-.346.1-.114.133-.198.198-.33.065-.134.034-.248-.015-.347-.05-.099-.445-1.076-.612-1.47-.16-.389-.323-.335-.445-.34-.114-.007-.247-.007-.38-.007a.729.729 0 0 0-.529.247c-.182.198-.691.677-.691 1.654 0 .977.71 1.916.81 2.049.098.133 1.394 2.132 3.383 2.992.47.205.84.326 1.129.418.475.152.904.129 1.246.08.38-.058 1.171-.48 1.338-.943.164-.464.164-.86.114-.943-.049-.084-.182-.133-.38-.232z" />
                  </svg>
                </button>
              </div>
            </div>

            {/* 이전/다음 포스트 네비게이션 */}
            <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-50 p-4 rounded-lg">
                <span className="text-sm text-gray-500">이전 포스트</span>
                <Link href="#" className="block font-medium text-blue-600 hover:text-blue-800">
                  이전 게시물 제목
                </Link>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg text-right">
                <span className="text-sm text-gray-500">다음 포스트</span>
                <Link href="#" className="block font-medium text-blue-600 hover:text-blue-800">
                  다음 게시물 제목
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

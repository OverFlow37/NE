import { Metadata } from 'next';
import Link from 'next/link';
import Image from 'next/image';
import { blogPosts } from '@/data/blog-posts';
import { formatDate } from '@/lib/utils';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

export const metadata: Metadata = {
  title: '개발자 노트',
  description: 'Project New Eden의 개발 과정과 최신 업데이트 소식을 확인하세요.',
};

export default function BlogPage() {
  // 블로그 포스트를 날짜순으로 정렬
  const sortedPosts = [...blogPosts].sort(
    (a, b) => new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime()
  );

  return (
    <div>
      {/* 블로그 헤더 */}
      <section className="bg-blue-900 text-white py-16">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6">개발자 노트</h1>
          <p className="text-xl max-w-3xl mx-auto">
            Project New Eden의 개발 과정과 최신 업데이트 소식을 확인하세요.
          </p>
        </div>
      </section>

      {/* 블로그 포스트 목록 */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-5xl mx-auto">
            {sortedPosts.length > 0 ? (
              <div className="grid grid-cols-1 gap-8">
                {sortedPosts.map((post) => (
                  <Card
                    key={post.id}
                    className="flex flex-col md:flex-row overflow-hidden hover:shadow-lg transition-shadow"
                  >
                    <div className="md:w-1/3 relative h-48 md:h-auto bg-gray-200">
                      <Image
                        src={post.featuredImage}
                        alt={post.title}
                        fill
                        style={{ objectFit: 'cover' }}
                        sizes="(max-width: 768px) 100vw, 33vw"
                      />
                    </div>
                    <div className="md:w-2/3 flex flex-col">
                      <CardHeader>
                        <CardTitle>
                          <Link
                            href={`/blog/${post.slug}`}
                            className="hover:text-blue-600 transition-colors"
                          >
                            {post.title}
                          </Link>
                        </CardTitle>
                        <CardDescription>
                          {formatDate(post.publishedAt)} • {post.authorName}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <p className="text-gray-600">{post.summary}</p>
                      </CardContent>
                      <CardFooter className="mt-auto">
                        <div className="flex justify-between items-center w-full">
                          <div className="flex flex-wrap gap-2">
                            {post.tags.map((tag) => (
                              <span
                                key={tag}
                                className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded"
                              >
                                #{tag}
                              </span>
                            ))}
                          </div>
                          <Link
                            href={`/blog/${post.slug}`}
                            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                          >
                            더 읽기 →
                          </Link>
                        </div>
                      </CardFooter>
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="text-center py-16">
                <div className="bg-gray-100 rounded-lg p-8 mx-auto max-w-lg">
                  <h2 className="text-2xl font-bold mb-4">아직 게시된 포스트가 없습니다</h2>
                  <p className="text-gray-600 mb-6">
                    곧 Project New Eden의 개발 소식과
                    <br /> 업데이트 정보가 이곳에 게시될 예정입니다.
                    <br />
                    조금만 기다려 주세요!
                  </p>
                  <Link
                    href="/"
                    className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg"
                  >
                    홈으로 돌아가기
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

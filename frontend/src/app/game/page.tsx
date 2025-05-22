import Image from 'next/image';
import Link from 'next/link';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: '게임 소개',
  description: '자율적 에이전트 에이전트와 로컬 LLM을 활용한 혁신적인 게임 세계',
};

export default function GamePage() {
  return (
    <div>
      {/* 게임 소개 헤더 */}
      <section className="bg-blue-900 text-white py-16">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6">Project New Eden 소개</h1>
          <p className="text-xl max-w-3xl mx-auto">
            Project New Eden는 로컬 LLM을 사용하여 유니티 게임 내 에이전트들에게 <br />
            지능적이고 다양한 행동을 부여하는 인공지능 시뮬레이션입니다.
          </p>
        </div>
      </section>

      {/* 비디오 섹션 */}
      {/* <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <div className="aspect-w-16 aspect-h-9 bg-gray-200 rounded-lg overflow-hidden">
              <iframe
                className="w-full h-[500px]"
                src="https://www.youtube.com/embed/"
                title="게임 트레일러"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              ></iframe>
            </div>
          </div>
        </div>
      </section> */}

      {/* 게임 개요 */}
      <section className="py-16 bg-gray-100">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row">
            <div className="md:w-1/2 mb-8 md:mb-0 md:pr-8">
              <h2 className="text-3xl font-bold mb-6">게임 개요</h2>
              <p className="mb-4">
                Project New Eden는 에이전트들이 지속적인 기억과 자연스러운 행동을 가지는 유니티 기반
                게임 세계입니다. 각 에이전트는 Gemma3 기반의 로컬 LLM을 통해 지능적인 의사결정을
                내리고, 환경과 상호작용합니다.
              </p>
              <p className="mb-4">
                이 시스템의 핵심은 에이전트의 경험을 저장하고 검색하는 메모리 시스템과, 과거 경험을
                바탕으로 행동을 결정하는 반응 시스템, 그리고 에이전트 간의 자연스러운 대화를
                생성하는 대화 시스템입니다.
              </p>
              <p>
                플레이어는 이러한 지능적인 에이전트들과 상호작용하면서 매번 새로운 경험을 할 수
                있습니다. 각 에이전트는 자신만의 성격, 목표, 기억을 가지고 있어 예측할 수 없는
                흥미로운 상황이 펼쳐집니다.
              </p>
            </div>
            <div className="md:w-1/2">
              <div className="grid grid-cols-2 gap-4">
                <div className="relative h-48 rounded-lg overflow-hidden bg-gray-300">
                  <Image
                    src="/images/screenshot1.jpg"
                    alt="게임 스크린샷 1"
                    fill
                    style={{ objectFit: 'cover' }}
                    sizes="(max-width: 768px) 100vw, 25vw"
                  />
                </div>
                <div className="relative h-48 rounded-lg overflow-hidden bg-gray-300">
                  <Image
                    src="/images/screenshot2.jpg"
                    alt="게임 스크린샷 2"
                    fill
                    style={{ objectFit: 'cover' }}
                    sizes="(max-width: 768px) 100vw, 25vw"
                  />
                </div>
                <div className="relative h-48 rounded-lg overflow-hidden bg-gray-300">
                  <Image
                    src="/images/screenshot3.jpg"
                    alt="게임 스크린샷 3"
                    fill
                    style={{ objectFit: 'cover' }}
                    sizes="(max-width: 768px) 100vw, 25vw"
                  />
                </div>
                <div className="relative h-48 rounded-lg overflow-hidden bg-gray-300">
                  <Image
                    src="/images/screenshot4.jpg"
                    alt="게임 스크린샷 4"
                    fill
                    style={{ objectFit: 'cover' }}
                    sizes="(max-width: 768px) 100vw, 25vw"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 핵심 특징 */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">핵심 특징</h2>
          <div className="max-w-4xl mx-auto">
            <div className="mb-8 pb-8 border-b border-gray-200">
              <h3 className="text-2xl font-semibold mb-4">완전 자율적인 에이전트</h3>
              <p>
                각 에이전트는 고유한 성격, 목표, 관계를 가지고 있으며, LLM을 통해 상황에 맞는
                의사결정을 자율적으로 내립니다. 이들은 기억을 형성하고, 관계를 발전시키며, 환경에
                적응하여 살아있는 가상 세계를 만들어냅니다.
              </p>
            </div>

            <div className="mb-8 pb-8 border-b border-gray-200">
              <h3 className="text-2xl font-semibold mb-4">로컬에서 작동하는 AI</h3>
              <p>
                Ollama를 통해 Gemma3 모델을 로컬에서 실행하여 인터넷 연결 없이도 고급 AI 기능을
                사용할 수 있습니다. 개인정보 보호와 빠른 응답 속도를 보장합니다.
              </p>
            </div>

            <div className="mb-8 pb-8 border-b border-gray-200">
              <h3 className="text-2xl font-semibold mb-4">복잡한 환경 상호작용</h3>
              <p>
                게임 세계의 환경은 에이전트의 행동에 영향을 미치고, 반대로 에이전트들은 자신의
                행동으로 환경을 변화시킵니다. 플레이어의 개입, 시간, 이벤트 등 다양한 요소가
                에이전트의 의사결정에 영향을 줍니다.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 다운로드 CTA */}
      <section className="py-16 bg-blue-900 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-6">지금 경험해보세요</h2>
          <p className="text-xl mb-8 max-w-2xl mx-auto">
            Project New Eden을 다운로드하고 <br />
            매번 새롭게 펼쳐지는 자율적인 가상 세계를 경험해보세요.
          </p>
          <Link
            href="/download"
            className="bg-white text-blue-900 hover:bg-gray-100 font-bold py-3 px-8 rounded-lg"
          >
            다운로드하기
          </Link>
        </div>
      </section>
    </div>
  );
}

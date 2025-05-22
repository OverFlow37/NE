import { Metadata } from 'next';
import Image from 'next/image';
import { agents } from '@/data/agents';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';

export const metadata: Metadata = {
  title: '에이전트',
  description: '로컬 LLM을 활용하는 자율적 에이전트 에이전트들을 만나보세요.',
};

export default function AgentsPage() {
  return (
    <div>
      {/* 에이전트 헤더 */}
      <section className="bg-blue-900 text-white py-16">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6">에이전트</h1>
          <p className="text-xl max-w-3xl mx-auto">
            Project New Eden의 지능적인 에이전트들을 만나보세요.
            <br /> 각 에이전트는 기억과 경험을 바탕으로 자율적으로 행동합니다.
          </p>
        </div>
      </section>

      {/* 에이전트 소개 */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {agents.map((agent) => (
              <Card key={agent.id} className="hover:shadow-lg transition-shadow duration-300">
                <CardHeader className="p-0">
                  <div className="relative h-64 w-full rounded-t-lg overflow-hidden bg-gray-200">
                    <Image
                      src={agent.imageUrl}
                      alt={agent.name}
                      fill
                      style={{ objectFit: 'cover' }}
                      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 25vw"
                    />
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  <CardTitle className="mb-2">{agent.name}</CardTitle>
                  <p className="text-sm text-blue-600 mb-2">{agent.role}</p>
                  <p className="text-gray-600 mb-4 line-clamp-3">{agent.description}</p>
                </CardContent>
                <CardFooter>
                  <span className="text-gray-400 text-sm">준비 중</span>
                </CardFooter>
              </Card>
            ))}

            <Card className="hover:shadow-lg transition-shadow duration-300 opacity-80 border-2 border-dashed border-gray-600">
              <CardHeader className="p-0">
                <div className="relative h-64 w-full rounded-t-lg overflow-hidden bg-gradient-to-r from-gray-200 to-gray-400 flex items-center justify-center">
                  <div className="text-white text-8xl font-bold">?</div>
                </div>
              </CardHeader>
              <CardContent className="pt-6 text-center">
                <p className="mb-2">새로운 에이전트가 추가될 예정입니다.</p>
                <p className="text-gray-600 mb-4">조금만 기다려 주세요.</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* 에이전트 인공지능 설명 */}
      <section className="py-16 bg-gray-100">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">에이전트 인공지능</h2>
          <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-md p-8">
            <h3 className="text-2xl font-semibold mb-4">Gemma3 기반 로컬 LLM</h3>
            <p className="mb-4">
              Project New Eden의 모든 에이전트는 Gemma3 기반의 로컬 LLM(소형 언어 모델)을 활용하여
              자율적인 의사결정을 내립니다. 이 모델은 로컬 컴퓨터에서 실행되어 인터넷 연결 없이도
              에이전트가 지능적으로 행동할 수 있게 합니다.
            </p>

            <h3 className="text-2xl font-semibold mb-4">에이전트 인공지능 메커니즘</h3>
            <p className="mb-4">
              Project New Eden의 에이전트는 단순한 스크립트가 아닌 지능적인 에이전트입니다. 이들은
              경험을 기억하고, 과거를 반성하며, 미래를 계획하는 복잡한 인지 구조를 가지고 있습니다.
            </p>

            <h3 className="text-2xl font-semibold mb-4 mt-8">단기기억과 장기기억</h3>
            <p className="mb-4">
              에이전트는 관찰, 행동, 피드백을 저장하는 단기기억과 반성과 통찰을 저장하는 장기기억을
              가집니다. 이러한 이중 메모리 구조를 통해 보다 복잡하고 일관된 행동 패턴을 형성하고,
              과거 경험을 바탕으로 더 나은 의사결정을 할 수 있습니다.
            </p>

            <h3 className="text-2xl font-semibold mb-4 mt-8">반응 및 행동 결정</h3>
            <p className="mb-4">
              각 에이전트는 주변 환경에서 발생하는 이벤트를 인식하고, 자신의 기억과 성격에 기반하여
              이에 반응할지 여부를 결정합니다. 반응을 결정할 경우 과거의 유사한 경험을 검색하여 가장
              적절한 행동을 생성합니다. 이 과정은 로컬 LLM을 통해 자연스럽고 맥락에 맞는 행동으로
              이어집니다.
            </p>

            <h3 className="text-2xl font-semibold mb-4 mt-8">반성과 계획</h3>
            <p className="mb-4">
              하루가 끝날 때 에이전트는 그날의 중요한 경험에 대해 반성하고 통찰을 생성합니다. 이러한
              반성은 다음 날의 계획 수립에 영향을 미치며, 보다 목적이 있고 일관된 행동 패턴을
              형성하게 합니다. 이렇게 에이전트는 단순히 환경에 반응하는 것을 넘어 자신만의 목표를
              가지고 행동하는 자율적인 존재가 됩니다.
            </p>

            {/* <h3 className="text-2xl font-semibold mb-4 mt-8">자연스러운 대화</h3>
            <p>
              에이전트들은 서로 대화할 수 있으며, 이 대화는 그들의 기억, 관계, 현재 상황에
              기반합니다. 각 에이전트는 자신의 성격과 이전 경험에 따라 고유한 대화 스타일을 가지며,
              대화 내용은 그들의 메모리에 저장되어 미래 상호작용에 영향을 미칩니다. 최대 4턴까지
              진행되는 대화는 자연스럽게 시작되고 종료되어 보다 현실적인 상호작용을 제공합니다.
            </p> */}
          </div>
        </div>
      </section>
    </div>
  );
}

import { Metadata } from 'next';
// import Image from 'next/image';
import Link from 'next/link';
import {
  FaServer,
  FaBrain,
  FaDatabase,
  FaCode,
  FaUserCog,
  // FaComments,
  //   FaCalendarAlt,
} from 'react-icons/fa';

export const metadata: Metadata = {
  title: '기술 구조',
  description: 'Project New Eden의 핵심 기술과 아키텍처에 대해 알아보세요.',
};

export default function TechnologyPage() {
  return (
    <div>
      {/* 기술 구조 헤더 */}
      <section className="bg-blue-900 text-white py-16">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6">기술 구조</h1>
          <p className="text-xl max-w-3xl mx-auto">
            Project New Eden의 핵심 기술과 아키텍처에 대해 알아보세요. <br /> 로컬 LLM과 메모리
            시스템이 어떻게 작동하여 지능적인 에이전트를 구현하는지 살펴봅니다.
          </p>
        </div>
      </section>

      {/* 프로젝트 개요 */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">프로젝트 목적</h2>
          <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-md p-8">
            <p className="mb-4">
              Project New Eden는 로컬 LLM(Ollama의 Gemma3)을 사용하여 유니티 게임 내 에이전트들에게
              지능적이고 다양한 행동을 부여하는 AI 시스템을 구현합니다. 주요 목표는 다음과 같습니다:
            </p>
            <ul className="list-disc list-inside space-y-2 text-gray-700 mb-6">
              <li>에이전트에게 기억과 경험을 바탕으로 한 자연스러운 행동 생성</li>
              {/* <li>에이전트 간 대화를 통한 상호작용 구현</li> */}
              <li>기억 관리 및 과거 경험을 반영한 계획 수립</li>
              <li>환경과 플레이어의 말에 대한 반응 생성</li>
            </ul>
            <p>
              이러한 목표를 달성함으로써, 게임 세계의 에이전트들이 마치 살아있는 것처럼 자율적으로
              행동하고 상호작용하며, 플레이어에게 보다 현실적이고 몰입감 있는 경험을 제공합니다.
            </p>
          </div>
        </div>
      </section>

      {/* 핵심 기능 */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">핵심 기능 및 모듈</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
            {/* 메모리 시스템 */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center mb-4">
                <div className="bg-blue-100 text-blue-600 p-3 rounded-full mr-4">
                  <FaDatabase className="text-xl" />
                </div>
                <h3 className="text-xl font-semibold">메모리 시스템</h3>
              </div>
              <p className="text-gray-700 mb-4">
                에이전트의 경험과 관찰을 저장하고 검색하는 시스템입니다. 단기기억과 장기기억으로
                구분되어 관리됩니다.
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-1">
                <li>
                  <strong>단기기억</strong>: 관찰, 행동, 피드백 정보를 저장
                </li>
                <li>
                  <strong>장기기억</strong>: 반성 및 통찰을 저장
                </li>
                <li>
                  <strong>MemoryUtils</strong>: 메모리 저장, 로드, 임베딩 생성
                </li>
                <li>
                  <strong>MemoryRetriever</strong>: 유사 메모리 검색 및 연결
                </li>
              </ul>
            </div>

            {/* 반응 시스템 */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center mb-4">
                <div className="bg-purple-100 text-purple-600 p-3 rounded-full mr-4">
                  <FaUserCog className="text-xl" />
                </div>
                <h3 className="text-xl font-semibold">반응 시스템</h3>
              </div>
              <p className="text-gray-700 mb-4">
                에이전트가 이벤트에 반응할지 여부를 결정하고 적절한 반응을 생성합니다.
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-1">
                <li>
                  <strong>ReactionDecider</strong>: 이벤트 중요도 평가 및 반응 여부 결정
                </li>
                <li>
                  <strong>반응 생성</strong>: 이벤트에 대한 구체적 반응 생성
                </li>
                <li>
                  <strong>행동 생성</strong>: 기억 기반 행동 결정
                </li>
                <li>
                  <strong>피드백 처리</strong>: 행동 결과 평가 및 저장
                </li>
              </ul>
            </div>

            {/* 대화 시스템 */}
            {/* <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center mb-4">
                <div className="bg-green-100 text-green-600 p-3 rounded-full mr-4">
                  <FaComments className="text-xl" />
                </div>
                <h3 className="text-xl font-semibold">대화 시스템</h3>
              </div>
              <p className="text-gray-700 mb-4">에이전트 간의 자연스러운 대화를 생성하고 관리합니다.</p>
              <ul className="list-disc list-inside text-gray-700 space-y-1">
                <li>
                  <strong>에이전트ConversationManager</strong>: 대화 세션 관리 및 발화 생성
                </li>
                <li>
                  <strong>대화 종료</strong>: 대화 종료 시점 결정 (최대 10턴)
                </li>
                <li>
                  <strong>메모리 통합</strong>: 대화 내용을 메모리에 저장
                </li>
                <li>
                  <strong>자연스러운 대화</strong>: 에이전트 성격과 상태 반영
                </li>
              </ul>
            </div> */}

            {/* 계획 및 반성 시스템 */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center mb-4">
                <div className="bg-red-100 text-red-600 p-3 rounded-full mr-4">
                  <FaBrain className="text-xl" />
                </div>
                <h3 className="text-xl font-semibold">계획 및 반성 시스템</h3>
              </div>
              <p className="text-gray-700 mb-4">
                에이전트의 계획 수립과 과거 경험에 대한 반성을 처리합니다.
              </p>
              <ul className="list-disc list-inside text-gray-700 space-y-1">
                <li>
                  <strong>계획 생성</strong>: 과거 경험을 바탕으로 미래 계획 수립
                </li>
                <li>
                  <strong>반성</strong>: 중요 경험에 대한 사고와 통찰 생성
                </li>
                <li>
                  <strong>하루 일과 계획</strong>: 시간별 활동 계획 생성
                </li>
                <li>
                  <strong>중요도 평가</strong>: 경험의 중요도 평가 및 분류
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* 메모리 시스템 상세 */}
      <section className="py-16 bg-gray-100">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">메모리 시스템 상세</h2>
          <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-md p-8">
            <h3 className="text-2xl font-semibold mb-6">메모리 구조</h3>

            <div className="mb-8">
              <h4 className="text-xl font-semibold mb-4">단기기억</h4>
              <p className="text-gray-700 mb-4">
                에이전트가 관찰한 이벤트 및 정보, 에이전트의 행동 및 피드백 정보를 자연어로 저장하고
                이후 반응과 반성에서 사용합니다.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h5 className="font-semibold mb-2 text-blue-700">관찰</h5>
                  <p className="text-sm text-gray-700">
                    에이전트가 주변 환경이나 이벤트를 목격했을 때 발생하는 기억. 이벤트는 반응을
                    유발할 수 있으며, 반응은 에이전트의 행동을 유발할 수 있습니다.
                  </p>
                </div>

                <div className="bg-green-50 p-4 rounded-lg">
                  <h5 className="font-semibold mb-2 text-green-700">행동(스케줄)</h5>
                  <p className="text-sm text-gray-700">
                    반응으로 행동을 생성할 때, 주변환경, 에이전트의 정보, 기존 기억을 참조합니다.
                    반응에 의해 생성된 행동은 단기기억에 저장되며 해당 행동의 결과가 피드백으로
                    생성됩니다.
                  </p>
                </div>

                <div className="bg-purple-50 p-4 rounded-lg">
                  <h5 className="font-semibold mb-2 text-purple-700">피드백</h5>
                  <p className="text-sm text-gray-700">
                    피드백은 행동에 대한 결과로 긍정, 부정적인 경험을 저장합니다. 이는 이후 행동
                    결정에 중요한 영향을 미칩니다.
                  </p>
                </div>
              </div>
            </div>

            <div className="mb-8">
              <h4 className="text-xl font-semibold mb-4">장기기억</h4>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div className="bg-amber-50 p-4 rounded-lg">
                  <h5 className="font-semibold mb-2 text-amber-700">반성</h5>
                  <p className="text-sm text-gray-700">
                    에이전트가 하루동안 저장된 단기기억을 통해 유의미한 정보를 분류하여 초점을
                    생성하고, 초점과 이전 반성을 기준으로 새로운 반성을 생성합니다. 생성된 반성은
                    이후 행동, 계획 생성에 사용됩니다.
                  </p>
                </div>

                <div className="bg-indigo-50 p-4 rounded-lg">
                  <h5 className="font-semibold mb-2 text-indigo-700">계획</h5>
                  <p className="text-sm text-gray-700">
                    에이전트의 하루 일과를 생성하여 하루동안 진행할 행동(스케줄)을 생성합니다.
                    당일의 반성과 전날의 계획을 참조하여 생성되며, 에이전트의 행동에 일정한 경향성을
                    부여합니다.
                  </p>
                </div>
              </div>
            </div>

            <h3 className="text-2xl font-semibold mb-6">유사한 기억 검색 방식</h3>
            <p className="text-gray-700 mb-4">
              유사한 기억을 찾을 때는 다음 세 가지 요소를 고려합니다:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 mb-6">
              <li>
                <strong>유사도</strong>: 임베딩 벡터 간 코사인 유사도 (0~1 사이 실수)
              </li>
              <li>
                <strong>중요도</strong>: 1~10 사이의 정수를 10으로 나누어 정규화
              </li>
              <li>
                <strong>최신성</strong>: 최근 기억에 더 높은 가중치 부여
              </li>
            </ul>
            <p className="text-gray-700">
              최종 가치 계산: <strong>유사도 × 5 + 중요도 × 2 + 최신성 × 2</strong>로 계산하여 가장
              관련성 높은 기억을 선별합니다.
            </p>
          </div>
        </div>
      </section>

      {/* 반응 및 행동 처리 */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">반응, 행동, 피드백 처리 흐름</h2>
          <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-md p-8">
            <p className="text-gray-700 mb-6">
              에이전트가 스스로 판단하여 움직이는 로직은 다음과 같은 흐름으로 처리됩니다:
            </p>

            <div className="space-y-8">
              <div className="flex flex-col md:flex-row gap-6">
                <div className="md:w-1/4 flex justify-center">
                  <div className="bg-blue-100 text-blue-700 rounded-full h-16 w-16 flex items-center justify-center text-2xl">
                    1
                  </div>
                </div>
                <div className="md:w-3/4">
                  <h4 className="text-xl font-semibold mb-2">이벤트 인식</h4>
                  <p className="text-gray-700">
                    평소에는 계획에 따라 행동하지만, 특정 이벤트를 관측하면 반응을 고려합니다.
                    이벤트는 메모리에 저장됩니다.
                  </p>
                </div>
              </div>

              <div className="flex flex-col md:flex-row gap-6">
                <div className="md:w-1/4 flex justify-center">
                  <div className="bg-green-100 text-green-700 rounded-full h-16 w-16 flex items-center justify-center text-2xl">
                    2
                  </div>
                </div>
                <div className="md:w-3/4">
                  <h4 className="text-xl font-semibold mb-2">반응 결정</h4>
                  <p className="text-gray-700">
                    이벤트에 반응할지 결정할 때, 단기기억에서 유사한 상황을 찾아 행동을 생성할지
                    말지 결정합니다. 이 과정에서 로컬 LLM 모델을 사용하여 이벤트에 대한 반응
                    필요성을 평가합니다.
                  </p>
                </div>
              </div>

              <div className="flex flex-col md:flex-row gap-6">
                <div className="md:w-1/4 flex justify-center">
                  <div className="bg-yellow-100 text-yellow-700 rounded-full h-16 w-16 flex items-center justify-center text-2xl">
                    3
                  </div>
                </div>
                <div className="md:w-3/4">
                  <h4 className="text-xl font-semibold mb-2">행동 생성</h4>
                  <p className="text-gray-700">
                    행동을 하기로 결정했다면, 다시 기억에서 유사한 상황을 찾아 현재 상태, 관련 기억,
                    환경 등을 기반으로 행동을 생성합니다. 이 과정에서도 LLM을 활용하여 맥락에 맞는
                    자연스러운 행동을 결정합니다.
                  </p>
                </div>
              </div>

              <div className="flex flex-col md:flex-row gap-6">
                <div className="md:w-1/4 flex justify-center">
                  <div className="bg-red-100 text-red-700 rounded-full h-16 w-16 flex items-center justify-center text-2xl">
                    4
                  </div>
                </div>
                <div className="md:w-3/4">
                  <h4 className="text-xl font-semibold mb-2">피드백 처리</h4>
                  <p className="text-gray-700">
                    행동을 수행한 후 결과에 대한 피드백을 생성하고 메모리에 저장합니다. 이 피드백은
                    향후 유사한 상황에서의 의사결정에 중요한 영향을 미칩니다. 예를 들어, 특정
                    오브젝트 사용에 대한 부정적 경험은 향후 해당 오브젝트에 대한 접근 방식을
                    변경하게 됩니다.
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-8 p-4 bg-gray-50 rounded-lg">
              <h4 className="text-lg font-semibold mb-2">기억 검색 중요도 계산 방식</h4>
              <p className="text-gray-700 text-sm">
                유사한 기억을 찾을 때 에이전트의 상태(욕구)와 이벤트를 기반으로 임베딩 벡터를
                생성하고, 기억의 가치를 3가지 항목(유사도, 중요도, 최신성)으로 정렬하여 가장 관련성
                높은 기억을 선택합니다. 반성 기억은 일반 기억보다 1.5배 더 높은 중요도 가중치를
                가집니다.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 반성 시스템 */}
      <section className="py-16 bg-gray-100">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">반성 시스템</h2>
          <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-md p-8">
            <p className="text-gray-700 mb-6">
              에이전트가 하루 동안의 경험을 통해 통찰(생각)을 도출하고 저장하는 과정입니다. 이 반성
              결과는 향후 행동과 계획에 영향을 미칩니다.
            </p>

            <div className="space-y-6">
              <div className="border-l-4 border-blue-500 pl-4">
                <h4 className="text-lg font-semibold mb-2">반성 생성 과정</h4>
                <ul className="list-disc list-inside text-gray-700 space-y-1">
                  <li>하루 동안 축적된 단기기억 중 중요도가 높은 메모리를 초점으로 선별</li>
                  <li>중요 메모리와 이전 반성이 포함된 단일 프롬프트로 배치 처리</li>
                  <li>LLM은 각 메모리에 대한 개별 반성을 일괄적으로 생성하고 JSON 형식으로 반환</li>
                  <li>각 메모리 별로 2-3 문장의 짧고 간결한 1인칭 시점 반성 생성</li>
                  <li>생성된 반성은 장기기억에 저장되어 이후 의사결정에 참조</li>
                </ul>
              </div>

              <div className="border-l-4 border-green-500 pl-4">
                <h4 className="text-lg font-semibold mb-2">반성 검색 방식</h4>
                <ul className="list-disc list-inside text-gray-700 space-y-1">
                  <li>유사도, 중요도, 최신성을 고려하여 관련 반성 검색</li>
                  <li>최종 관련성 점수: (최신성 × 0.7) + (중요도 × 0.3)</li>
                  <li>관련성 점수 기준 내림차순 정렬 후 상위 5개를 참조</li>
                </ul>
              </div>

              <div className="border-l-4 border-purple-500 pl-4">
                <h4 className="text-lg font-semibold mb-2">임베딩 생성 방식</h4>
                <ul className="list-disc list-inside text-gray-700 space-y-1">
                  <li>반성의 이벤트와 통찰(thought)을 기반으로 임베딩 생성</li>
                  <li>토큰화 및 소문자 변환 후 word2vec 모델 단어 추출</li>
                  <li>단어 벡터들의 평균을 계산하여 문장 벡터로 사용</li>
                  <li>벡터 정규화를 통해 크기가 1인 단위 벡터로 변환</li>
                </ul>
              </div>
            </div>

            <div className="mt-8 p-4 bg-blue-50 rounded-lg">
              <h4 className="text-lg font-semibold mb-2 text-blue-700">반성 예시</h4>
              <p className="text-gray-700 italic">
                &quot;오늘 숲에서 사과를 발견했을 때, 나는 매우 기뻤다. 이전에 맛있는 열매를 찾아
                실패했던 경험이 있었는데, 이번에는 성공해서 만족스러웠다. 앞으로도 숲을 더 자주
                탐험하면 다양한 식량을 찾을 수 있을 것 같다.&quot;
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 계획 시스템 */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">계획 시스템</h2>
          <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-md p-8">
            <p className="text-gray-700 mb-6">
              에이전트가 하루 동안의 활동을 계획하는 시스템으로, 과거 경험과 반성을 바탕으로 미래
              행동을 결정합니다.
            </p>

            <div className="mb-8">
              <h4 className="text-xl font-semibold mb-4">계획 생성 우선순위</h4>
              <ol className="list-decimal list-inside text-gray-700 space-y-1 mb-4">
                <li>금일 반성 결과 기반 활동</li>
                <li>금일 기존 계획</li>
                <li>과거 고중요도 활동</li>
              </ol>
              <p className="text-gray-700 text-sm">
                이러한 우선순위를 바탕으로 에이전트의 일과가 결정되며, 계획은 겹치지 않고 연속적으로
                배치됩니다. 기본적으로 기상 시간은 06:00, 취침 시간은 24:00으로 설정되며, 식사
                시간은 규칙적으로 배치됩니다.
              </p>
            </div>

            <div>
              <h4 className="text-xl font-semibold mb-4">중요도 점수 체계</h4>
              <div className="overflow-x-auto">
                <table className="min-w-full border border-gray-200">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="py-2 px-4 border">점수 범위</th>
                      <th className="py-2 px-4 border">의미</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="py-2 px-4 border">1–3</td>
                      <td className="py-2 px-4 border">일상적인 소소한 활동 (예: 정리, 걷기 등)</td>
                    </tr>
                    <tr>
                      <td className="py-2 px-4 border">4–6</td>
                      <td className="py-2 px-4 border">
                        일상에서 얻는 중간 정도의 인사이트 있는 경험
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2 px-4 border">7–8</td>
                      <td className="py-2 px-4 border">개인적으로 의미 있는 경험이나 성찰</td>
                    </tr>
                    <tr>
                      <td className="py-2 px-4 border">9–10</td>
                      <td className="py-2 px-4 border">인생을 바꿀 만한 중요한 결정이나 경험</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 특징 및 장점 */}
      <section className="py-16 bg-gray-100">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">특징 및 장점</h2>
          <div className="max-w-4xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-xl font-semibold mb-4 text-blue-600">메모리 기반 행동</h3>
                <p className="text-gray-700">
                  에이전트가 과거 경험을 기억하고 이를 바탕으로 행동하여 일관성 있고 지능적인
                  상호작용을 제공합니다.
                </p>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-xl font-semibold mb-4 text-green-600">자연스러운 대화</h3>
                <p className="text-gray-700">
                  에이전트 성격과 상태를 반영한 대화 생성으로 보다 현실적이고 몰입감 있는 상호작용이
                  가능합니다.
                </p>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-xl font-semibold mb-4 text-purple-600">Word2Vec 임베딩</h3>
                <p className="text-gray-700">
                  효율적인 의미 기반 메모리 검색으로 맥락에 맞는 행동과 반응을 생성할 수 있습니다.
                </p>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-xl font-semibold mb-4 text-red-600">로컬 LLM 활용</h3>
                <p className="text-gray-700">
                  Ollama의 Gemma3 모델을 사용하여 인터넷 연결 없이도 빠르고 안정적인 AI 응답을
                  제공합니다.
                </p>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-xl font-semibold mb-4 text-amber-600">데이터 지속성</h3>
                <p className="text-gray-700">
                  모든 메모리와 대화가 파일로 저장되어 게임 세션 간 지속성을 유지하고 발전하는
                  에이전트 행동을 가능하게 합니다.
                </p>
              </div>

              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-xl font-semibold mb-4 text-indigo-600">자율적 대화</h3>
                <p className="text-gray-700">
                  컨텍스트에 맞게 자연스럽게 대화를 시작하고 종료하여 보다 현실적인 에이전트
                  상호작용을 제공합니다.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 기술 스택 */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">기술 스택</h2>
          <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-md p-8">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="bg-blue-100 text-blue-600 p-4 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-4">
                  <FaServer className="text-3xl" />
                </div>
                <h3 className="font-semibold mb-1">서버</h3>
                <p className="text-gray-600 text-sm">FastAPI</p>
              </div>

              <div className="text-center">
                <div className="bg-purple-100 text-purple-600 p-4 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-4">
                  <FaBrain className="text-3xl" />
                </div>
                <h3 className="font-semibold mb-1">LLM</h3>
                <p className="text-gray-600 text-sm">Ollama (Gemma3)</p>
              </div>

              <div className="text-center">
                <div className="bg-green-100 text-green-600 p-4 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-4">
                  <FaDatabase className="text-3xl" />
                </div>
                <h3 className="font-semibold mb-1">임베딩</h3>
                <p className="text-gray-600 text-sm">Word2Vec</p>
              </div>

              <div className="text-center">
                <div className="bg-red-100 text-red-600 p-4 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-4">
                  <FaCode className="text-3xl" />
                </div>
                <h3 className="font-semibold mb-1">클라이언트</h3>
                <p className="text-gray-600 text-sm">Unity)</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 bg-blue-900 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-6">지능적인 에이전트와 상호작용해보세요</h2>
          <p className="text-xl mb-8 max-w-2xl mx-auto">
            Project New Eden를 다운로드하고 기억, 반성, 계획을 가진 지능적인 에이전트들이 만들어내는
            살아있는 가상 세계를 경험해보세요.
          </p>
          <Link
            href="/download"
            className="bg-white text-blue-900 hover:bg-gray-100 font-bold py-3 px-8 rounded-lg"
          >
            지금 다운로드
          </Link>
        </div>
      </section>
    </div>
  );
}

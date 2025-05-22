import { GameFeature } from '@/types';

export const gameFeatures: GameFeature[] = [
  {
    id: '1',
    title: '메모리 시스템',
    description:
      '에이전트가 경험과 관찰을 저장하고 검색하는 지능적인 메모리 시스템으로 과거 경험을 기억하고 이를 바탕으로 행동합니다.',
    iconName: 'Database',
  },
  {
    id: '2',
    title: '반응 시스템',
    description:
      '에이전트가 이벤트에 반응할지 여부를 결정하고 적절한 반응을 생성하여 자연스럽고 다양한 행동을 보여줍니다.',
    iconName: 'Users',
  },
  {
    id: '3',
    title: '계획 및 반성 시스템',
    description:
      '에이전트가 과거 경험을 바탕으로 미래 계획을 수립하고, 중요 경험에 대한 사고와 통찰을 생성합니다.',
    iconName: 'Brain',
  },
  {
    id: '4',
    title: '로컬 LLM 활용',
    description:
      'Ollama의 Gemma3 모델을 사용하여 인터넷 연결 없이도 고급 AI 기능을 제공하며, 개인정보를 보호합니다.',
    iconName: 'Shield',
  },
  {
    id: '5',
    title: '데이터 지속성',
    description:
      '모든 메모리와 대화가 파일로 저장되어 게임 세션 간 지속성을 유지하고, 지속적으로 발전하는 에이전트 행동을 경험할 수 있습니다.',
    iconName: 'HardDrive',
  },
  // {
  //   id: '6',
  //   title: '대화 시스템',
  //   description:
  //     '에이전트 간의 자연스러운 대화를 생성하고 관리하며, 대화 내용이 메모리에 저장되어 미래 행동에 영향을 줍니다.',
  //   iconName: 'MessageCircle',
  // },
];

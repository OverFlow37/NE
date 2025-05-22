// import Link from 'next/link';
import { Metadata } from 'next';
import { FaWindows, FaApple, FaLinux, FaDownload } from 'react-icons/fa';
import { systemRequirements } from '@/data/download-options';
// import { CURRENT_VERSION } from '@/lib/constants';

export const metadata: Metadata = {
  title: '다운로드',
  description:
    'AI 에이전트 시뮬레이션을 다운로드하고 설치하여 혁신적인 AI 기반 게임 세계를 경험해보세요.',
};

export default function DownloadPage() {
  return (
    <div>
      {/* 다운로드 헤더 */}
      <section className="bg-blue-900 text-white py-16">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6">다운로드</h1>
          <p className="text-xl max-w-3xl mx-auto">
            AI 에이전트 시뮬레이션을 다운로드하고 설치하여 <br /> 혁신적인 AI 기반 게임 세계를
            경험해보세요.
          </p>
        </div>
      </section>

      {/* 시스템 요구사항 */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">시스템 요구사항</h2>
          <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4 border-b pb-2">최소 사양</h3>
              <ul className="space-y-3">
                <li>
                  <strong>OS:</strong> {systemRequirements[0].os}
                </li>
                <li>
                  <strong>프로세서:</strong> {systemRequirements[0].processor}
                </li>
                <li>
                  <strong>메모리:</strong> {systemRequirements[0].memory}
                </li>
                <li>
                  <strong>그래픽:</strong> {systemRequirements[0].graphics}
                </li>
                <li>
                  <strong>저장공간:</strong> {systemRequirements[0].storage}
                </li>
                <li>
                  <strong>기타:</strong> {systemRequirements[0].additionalNotes}
                </li>
              </ul>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold mb-4 border-b pb-2">권장 사양</h3>
              <ul className="space-y-3">
                <li>
                  <strong>OS:</strong> {systemRequirements[1].os}
                </li>
                <li>
                  <strong>프로세서:</strong> {systemRequirements[1].processor}
                </li>
                <li>
                  <strong>메모리:</strong> {systemRequirements[1].memory}
                </li>
                <li>
                  <strong>그래픽:</strong> {systemRequirements[1].graphics}
                </li>
                <li>
                  <strong>저장공간:</strong> {systemRequirements[1].storage}
                </li>
                <li>
                  <strong>기타:</strong> {systemRequirements[1].additionalNotes}
                </li>
              </ul>
            </div>
          </div>

          <div className="max-w-4xl mx-auto mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-2 text-yellow-800">특별 요구사항: Ollama</h3>
            <p className="mb-2">
              AI 에이전트 시뮬레이션은 Ollama를 통해 Gemma3 모델을 실행합니다. 게임을 설치하기 전에
              먼저 Ollama를 설치해주세요.
            </p>
            <p>
              <a
                href="https://ollama.ai/download"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 font-semibold"
              >
                Ollama 다운로드 →
              </a>
            </p>
          </div>
        </div>
      </section>

      {/* 다운로드 링크 */}
      <section className="py-16 bg-gray-100">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">게임 다운로드</h2>
          <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Windows 다운로드 카드 */}
            <div className="bg-white rounded-lg shadow-md p-6 text-center">
              <div className="text-5xl text-blue-600 mb-4 flex justify-center">
                <FaWindows />
              </div>
              <h3 className="text-xl font-semibold mb-2">Windows</h3>
              <p className="text-gray-600 mb-4">버전 1.0.0</p>
              <a
                href="/downloads/ProjectNewEden-Win-v1.0.0.zip"
                className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg inline-flex items-center"
              >
                <FaDownload className="mr-2" /> 다운로드
              </a>
              <p className="text-sm text-gray-500 mt-2">54.8 MB</p>
            </div>

            {/* macOS 다운로드 카드 (비활성화) */}
            <div className="bg-white rounded-lg shadow-md p-6 text-center opacity-60">
              <div className="text-5xl text-gray-400 mb-4 flex justify-center">
                <FaApple />
              </div>
              <h3 className="text-xl font-semibold mb-2">macOS</h3>
              <p className="text-gray-600 mb-4">추후 지원 예정</p>
              <button
                disabled
                className="bg-gray-400 cursor-not-allowed text-white font-bold py-2 px-4 rounded-lg inline-flex items-center"
              >
                <FaDownload className="mr-2" /> 준비 중
              </button>
            </div>

            {/* Linux 다운로드 카드 (비활성화) */}
            <div className="bg-white rounded-lg shadow-md p-6 text-center opacity-60">
              <div className="text-5xl text-gray-400 mb-4 flex justify-center">
                <FaLinux />
              </div>
              <h3 className="text-xl font-semibold mb-2">Linux</h3>
              <p className="text-gray-600 mb-4">추후 지원 예정</p>
              <button
                disabled
                className="bg-gray-400 cursor-not-allowed text-white font-bold py-2 px-4 rounded-lg inline-flex items-center"
              >
                <FaDownload className="mr-2" /> 준비 중
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 설치 가이드 */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">설치 가이드</h2>
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-lg shadow-md p-8">
              <h3 className="text-2xl font-semibold mb-6">설치 단계</h3>

              <div className="mb-8">
                <h4 className="text-lg font-semibold mb-3">1. Python 3.11</h4>
                <p className="mb-4">
                  <a
                    href="https://www.python.org/downloads/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800"
                  >
                    Python 웹사이트
                  </a>
                  에서 Python 3.11 버전을 다운로드하고 설치합니다.
                </p>
              </div>

              <div className="mb-8">
                <h4 className="text-lg font-semibold mb-3">2. NVIDIA 그래픽 드라이버 설치하기</h4>
                <p className="mb-4">
                  <a
                    href="https://www.nvidia.com/ko-kr/drivers/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800"
                  >
                    NVIDIA 웹사이트
                  </a>
                  에서 그래픽카드와 호환되는 드라이버를 다운로드하고 설치합니다.
                </p>
              </div>

              <div className="mb-8">
                <h4 className="text-lg font-semibold mb-3">3. CUDA와 cuDNN 설치하기</h4>
                <p className="mb-4">
                  <a
                    href="https://developer.nvidia.com/cuda-toolkit-archive"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800"
                  >
                    NVIDIA Developer 웹사이트
                  </a>
                  에서 그래픽카드에 호환되는 CUDA를 다운로드하고 설치합니다.
                </p>
              </div>

              <div className="mb-8">
                <h4 className="text-lg font-semibold mb-3">4. Ollama 설치하기</h4>
                <p className="mb-4">
                  <a
                    href="https://ollama.ai/download"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800"
                  >
                    Ollama 웹사이트
                  </a>
                  에서 운영체제에 맞는 Ollama를 다운로드하고 설치합니다.
                </p>
                <div className="bg-gray-100 p-4 rounded-md">
                  <code className="text-sm">
                    # Ollama 설치 후 Gemma3 모델 다운로드
                    <br />
                    ollama pull gemma3
                  </code>
                </div>
              </div>

              <div className="mb-8">
                <h4 className="text-lg font-semibold mb-3">5. 게임 설치하기</h4>
                <p className="mb-2">Windows:</p>
                <ul className="list-disc pl-6 mb-4">
                  <li>다운로드한 ZIP 파일을 원하는 위치에 압축 해제합니다.</li>
                  <li>
                    압축 해제된 폴더 내의 <code>RunNewEden.bat</code>를 실행합니다.
                  </li>
                </ul>
              </div>

              <div>
                <h4 className="text-lg font-semibold mb-3">6. 게임 설정</h4>
                <p className="mb-4">
                  게임을 처음 실행하면 Ollama 연결 설정이 필요합니다. 기본 설정은 대부분의 경우
                  작동하지만, 다음과 같이 확인하거나 수정할 수 있습니다:
                </p>
                <div className="bg-gray-100 p-4 rounded-md mb-4">
                  <p className="mb-2">
                    <strong>Ollama API URL:</strong> http://localhost:11434
                  </p>
                  <p>
                    <strong>사용 모델:</strong> gemma3
                  </p>
                </div>
                <p>설정을 저장한 후 게임을 즐기시면 됩니다!</p>
              </div>
            </div>

            {/* <div className="text-center mt-8">
              <Link
                href="/faq"
                className="inline-flex items-center text-blue-600 hover:text-blue-800 font-semibold"
              >
                <FaQuestionCircle className="mr-2" /> 설치 문제 해결 및 FAQ
              </Link>
            </div> */}
          </div>
        </div>
      </section>
    </div>
  );
}

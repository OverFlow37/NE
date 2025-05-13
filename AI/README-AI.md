# AI 서버 실행 가이드

## 기본 실행 방법
1. `run_all.bat` 파일을 더블클릭하여 실행합니다.
   - 이 스크립트는 Ollama 서버와 AI 서버를 자동으로 시작합니다.

## 오류 발생 시 실행 방법
만약 `run_all.bat` 실행 시 오류가 발생한다면, 다음 단계를 따라 수동으로 서버를 실행해주세요:

1. Ollama 서버 상태 확인
   ```bash
   ollama list
   ```
   - 이 명령어로 Ollama 서버가 정상적으로 실행 중인지 확인할 수 있습니다.
   - 만약 오류가 발생한다면 Ollama 서버를 재시작해주세요.

2. AI 서버 수동 실행
   ```bash
   cd server
   python run_server.py
   ```
   - 이 명령어로 AI 서버를 직접 실행할 수 있습니다.

## 주의사항
- Ollama 서버가 실행 중이어야 AI 서버가 정상적으로 작동합니다.
- 서버 실행 전에 필요한 Python 패키지가 모두 설치되어 있는지 확인해주세요.
- 오류 메시지가 발생하면 콘솔 창의 로그를 확인해주세요.

## 문제 해결
1. Ollama 서버 연결 오류
   - Ollama 서버가 실행 중인지 확인
   - `ollama list` 명령어로 서버 상태 확인
   - 필요한 경우 Ollama 서버 재시작

2. AI 서버 실행 오류
   - Python 환경이 올바르게 설정되어 있는지 확인
   - 필요한 패키지가 모두 설치되어 있는지 확인
   - 서버 로그를 확인하여 구체적인 오류 원인 파악

## 문제 해결이 안되면 바로 mm이나 톡해주세요.

## 프로젝트 구조

### agent 폴더
에이전트의 핵심 로직과 데이터를 포함하는 폴더입니다.

```
agent/
├── config/           # 설정 파일들
│   └── paths.json    # 경로 설정
├── data/            # 데이터 저장소
│   ├── memories.json    # 에이전트의 메모리
│   ├── plans.json       # 계획 데이터
│   └── reflections.json # 반영 데이터
├── modules/         # 핵심 모듈
│   ├── memory_utils.py  # 메모리 관리 유틸리티
│   ├── ollama_client.py # Ollama API 클라이언트
│   └── retrieve.py      # 메모리 검색 및 처리
└── prompts/         # 프롬프트 템플릿
    └── retrieve/    # 검색 관련 프롬프트
        ├── retrieve_prompt.txt  # 검색 프롬프트
        └── retrieve_system.txt  # 시스템 프롬프트
```

#### 주요 모듈 설명
1. `memory_utils.py`
   - 메모리 저장 및 검색
   - Word2Vec 기반 임베딩 생성
   - 이벤트-문장 변환

2. `ollama_client.py`
   - Ollama API 통신
   - 프롬프트 처리
   - 응답 파싱

3. `retrieve.py`
   - 유사 메모리 검색
   - 코사인 유사도 계산
   - 프롬프트 생성

### server 폴더
FastAPI 기반의 웹 서버 구현을 포함하는 폴더입니다.

```
server/
├── run_server.py    # 서버 실행 스크립트
├── server.py        # 메인 서버 코드
└── tests/          # 테스트 코드
    └── memory_ollama_pipeline.py  # 메모리 파이프라인 테스트
```

#### 주요 파일 설명
1. `server.py`
   - FastAPI 엔드포인트 구현
   - 이벤트 처리 및 응답 생성
   - 메모리 저장 및 검색 통합

2. `run_server.py`
   - 서버 실행 설정
   - 포트 및 호스트 설정
   - 로깅 설정

3. `memory_ollama_pipeline.py`
   - 메모리 처리 파이프라인 테스트
   - 임베딩 생성 테스트
   - Ollama API 통신 테스트

## ✅ 버전 정보

- ### Unity

---

- ### AI

  - `ollama v0.7.0` - 모델 : **GEMMA3**
  - `fastapi`
  - `gensim` - 모델 : **word2vec-google-news-300**
  - `python 3.11.9`

---

## 🛠️ 사전 준비 사항

### 1. NVIDIA 그래픽 드라이버 설치

1. [NVIDIA 드라이버 다운로드](https://www.nvidia.co.kr/Download/index.aspx?lang=kr) 페이지로 이동
2. 자신의 **그래픽 카드**에 맞는 드라이버 검색
3. 드라이버 다운로드 후 설치

### 2. CUDA 설치

1. 터미널(cmd 또는 PowerShell)에서 아래 명령어 실행:

   ```bash
   nvidia-smi
   ```

2. 출력되는 정보에서 **CUDA 버전** 확인

3. 권장 CUDA 버전: **11.8**

> ⚠️ CUDA 버전은 사용하는 GPU 및 드라이버에 따라 다르므로, `nvidia-smi` 결과에 맞춰 설치

---

## 🦙 Ollama 설치 및 모델 다운로드

### 1. Ollama 설치

- 공식 사이트: [https://ollama.com/download](https://ollama.com/download)
- 자신의 OS에 맞는 설치 파일 다운로드 및 설치

### 2. 모델 실행 및 다운로드

1. 터미널(cmd)에서 아래 명령어 입력:

   ```bash
   ollama run gemma3
   ```

2. `gemma3` 모델이 다운로드되며, 완료 후 `/bye` 입력 창이 뜨면 정상 설치 완료

---

## 🔗 기타 참고 사항

- `gensim`은 `word2vec-google-news-300` 모델과 함께 사용되므로, 처음 실행 시 모델을 다운로드 받는 데 시간이 걸릴 수 있음
- `fastapi`는 서버 API 구성에 사용되며, 별도로 `uvicorn` 등의 실행 도구가 필요할 수 있음

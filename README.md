# 🗿 Project: New Eden

**AI를 통해 스스로 생각하고 움직이는 자율 에이전트를 신이 되어 관찰해 보세요, 에이전트를 도와주거나 방해하거나 선택은 당신의 몫입니다.**

---

![Image](https://github.com/user-attachments/assets/82614633-23f7-485b-b410-754c10cb80b1)

<br>

## 📜 프로젝트 소개 (About the Project)

**'Project: New Eden'** 은 샌드박스형 갓 게임(God Game)입니다. 플레이어는 신이 되어 무인도에서 생존하는 자율 AI 에이전트를 관찰하고 때로는 돕거나 방해하며 문명을 발전시켜 나갑니다. 에이전트들은 욕구와 기억에 따라 실제 살아있는 생명체처럼 생각하고 움직입니다.

<br>

## ✨ 주요 특징 (Key Features)

### 🧐 관찰 (Observation)
- 자율적으로 행동하는 AI 에이전트들이 섬을 탐색하고, 자원을 수집하며 생존하는 모습을 지켜볼 수 있습니다.
- 에이전트들은 '신(플레이어)'을 숭배하고 기도를 통해 신에게 여러 요청을 하기도 합니다.

### 🙏 개입 (Intervention)
- **권능**: 식량의 축복을 내려 에이전트에게 음식을 주거나 번개를 내려쳐 천벌을 내릴 수도 있습니다, 에이전트는 이러한 사건들을 기억합니다.
- **계시**: 에이전트에게 직접 프롬프트를 입력하여 대화를 시도하거나 명령을 내릴 수 있습니다.

### 🌱 생존과 발전 (Survival & Progression)
- 에이전트들은 생존을 위해 식량과 휴식이 필요하며, 이는 월드의 자원을 소모시킵니다. 플레이어는 무너지는 생태계의 균형을 유지해야 합니다.
- 나무, 광물 등 자원을 모아 새로운 건물을 해금하고, 원시적인 마을을 점차 발전시킬 수 있습니다.

<br>

## 🤖 핵심 기술: 자율 AI 에이전트 (Core Tech: Autonomous AI Agents)

본 프로젝트의 핵심은 SLM을 기반으로 한 자율 에이전트입니다. 에이전트는 단순히 정해진 로직을 따르는 것이 아니라, 기억을 바탕으로 스스로 판단하고 행동 계획을 수정합니다.

### 🧠 기억과 학습 (Memory & Learning)
에이전트는 모든 경험(관찰, 대화, 행동)을 **메모리 스트림**에 저장합니다. 하루의 끝에는 **'반성'** 과정을 통해 단순한 기억들을 고차원적이고 추상적인 지식으로 발전시켜 장기적인 행동에 영향을 줍니다.

### 🗓️ 동적 스케줄링 (Dynamic Scheduling)
에이전트는 기억을 바탕으로 하루의 계획을 세우지만, 이는 절대적이지 않습니다. 예상치 못한 상황이 발생하면 **'반응'** 시스템이 작동하여 실시간으로 스케줄을 수정합니다. 예를 들어, 먹으려던 음식이 갑자기 사라졌다면 즉시 다른 음식을 찾는 것으로 계획을 변경합니다.

### ⚡ 반응 시스템 (Reaction System)
에이전트는 주변 환경의 변화에 '흥미도'를 느낍니다. 처음 보는 오브젝트, 다른 에이전트의 접근, 플레이어의 '권능' 사용 등 특정 조건이 충족되면 현재 행동을 멈추고 새로운 행동을 결정하기 위한 AI 판단에 들어갑니다. 이는 에이전트가 살아있는 생명체처럼 느껴지게 하는 핵심 요소입니다.

<br>

## 🛠️ 기술 스택 (Tech Stack)

![Unity](https://img.shields.io/badge/unity-%23000000.svg?style=for-the-badge&logo=unity&logoColor=white)
![C#](https://img.shields.io/badge/c%23-%23239120.svg?style=for-the-badge&logo=csharp&logoColor=white) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
<img src="https://img.shields.io/badge/ollama-000000?style=for-the-badge&logo=ollama&logoColor=white" style="border-radius:10px">
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Git](https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white) ![GitLab](https://img.shields.io/badge/gitlab-%23181717.svg?style=for-the-badge&logo=gitlab&logoColor=white)

<br>

## 🚀 시작하기 (Getting Started)

이 프로젝트를 로컬 환경에서 실행하려면 아래의 안내를 따라주세요.

### 사전 요구사항 (Prerequisites)
* Python 3.11 버전 설치
* NVIDIA 그래픽 드라이버 설치
* CUDA 설치
* Ollama 설치

### 설치 (Installation)
자세한 설치 방법은 [링크 참조](https://github.com/OverFlow37/NE/blob/master/exec/1_%EB%B9%8C%EB%93%9C_%EB%B0%8F_%EB%B0%B0%ED%8F%AC_%EC%A0%95%EB%A6%AC_%EB%AC%B8%EC%84%9C.md)

<br>

## 👨‍👩‍👧‍👦 팀원 (Contributors)

| 이름 | 역할 | GitHub |
| :--: | :--: | :--: |
| **권오준** | 팀장, 개발 총괄 | [@github_id](https://github.com/github_id) |
| **김세희** | 유니티 3D | [@github_id](https://github.com/github_id) |
| **서영은** | 유니티 3D | [@github_id](https://github.com/github_id) |
| **강신우** | AI 총괄 | [@github_id](https://github.com/github_id) |
| **고형주** | AI | [@github_id](https://github.com/github_id) |
| **김주영** | AI | [@github_id](https://github.com/github_id) |

<br>

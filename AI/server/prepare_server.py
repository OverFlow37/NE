import os
import sys
import time
import gensim.downloader as api
from gensim.models import KeyedVectors
import subprocess
from pathlib import Path

def get_gensim_data_path():
    """gensim 모델 다운로드 기본 경로를 반환합니다"""
    try:
        # gensim 다운로더의 기본 경로 확인
        gensim_cache_dir = api.base_dir
        return gensim_cache_dir
    except Exception as e:
        return f"기본 경로 확인 중 오류 발생: {e}"

def prepare_model():
    """Word2Vec 모델을 준비하는 함수"""
    print("\n===== AI 서버 준비 프로그램 =====")
    print("이 프로그램은 AI 모델을 설치합니다.")
    
    # gensim 다운로드 기본 경로 출력
    gensim_path = get_gensim_data_path()
    print(f"\n📂 Gensim 모델 다운로드 기본 경로: {gensim_path}")
    print(f"📂 Word2Vec 모델 다운로드 위치: {os.path.join(gensim_path, 'word2vec-google-news-300')}")
    
    start_time = time.time()
    
    # 모델 저장 경로 설정
    current_dir = Path(__file__).parent
    KV_PATH = os.path.join(current_dir, 'models', 'word2vec-google-news-300.kv')
    
    # 1. KV 파일 존재 여부 확인
    if os.path.exists(KV_PATH):
        print(f"\n✅ Word2Vec 모델이 이미 설치되어 있습니다. ({KV_PATH})")
        return True
    else:
        # 2. KV 파일이 없으면 다운로드 및 변환
        print(f"\n❌ Word2Vec 모델이 설치되어 있지 않습니다.")
        print(f"⏳ Word2Vec 모델 다운로드 및 변환을 시작합니다...")
        print(f"⚠️ 이 작업은 처음 한 번만 수행되며, 약 1~3GB의 데이터를 다운로드하고 변환합니다.")
        print(f"⚠️ 네트워크 환경에 따라 수 분에서 수십 분이 소요될 수 있습니다.")
        
        try:
            # api.load로 다운로드된 .bin 파일 경로 가져오기
            print("\n🔽 Word2Vec 모델 다운로드 중...")
            bin_path = api.load('word2vec-google-news-300', return_path=True)
            print(f"✅ 다운로드 완료")
            print(f"📂 다운로드된 모델 경로: {bin_path}")
            
            # 바이너리 포맷(.bin) 로드
            print("\n🔄 모델 로드 및 변환 중...")
            kv = KeyedVectors.load_word2vec_format(bin_path, binary=True)
            
            # 디렉토리 생성 후 저장
            os.makedirs(os.path.dirname(KV_PATH), exist_ok=True)
            print(f"💾 KV 형식으로 저장 중... ({KV_PATH})")
            kv.save(KV_PATH)
            print("✅ 모델 변환 및 저장 완료")
            
            # 총 소요 시간 계산
            total_time = time.time() - start_time
            print(f"\n⏱ 총 모델 준비 시간: {total_time:.2f}초")
            
            return True
            
        except Exception as e:
            print(f"\n❌ 모델 다운로드 중 오류 발생: {e}")
            print("프로그램을 종료합니다.")
            input("계속하려면 아무 키나 누르세요...")
            return False

def start_server():
    """서버를 백그라운드로 시작하는 함수"""
    print("\n🚀 AI 서버를 시작합니다...")
    
    # 현재 실행 중인 스크립트의 경로 확인
    current_dir = Path(__file__).parent
    
    # Python 실행 경로 확인
    python_executable = sys.executable
    server_path = os.path.join(current_dir, "server.py")
    
    try:
        # server.py 백그라운드로 실행
        if os.name == 'nt':  # Windows
            # 콘솔창 안보이게 설정 - CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen([python_executable, server_path], 
                            creationflags=0x08000000)
        else:  # Unix/Linux
            subprocess.Popen([python_executable, server_path],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
        
        print("✅ AI 서버가 백그라운드에서 시작되었습니다.")
        return True
        
    except Exception as e:
        print(f"\n❌ 서버 실행 중 오류 발생: {e}")
        print("프로그램을 종료합니다.")
        input("계속하려면 아무 키나 누르세요...")
        return False

def main():
    """메인 함수 - 모델 준비 및 서버 시작"""
    start_time = time.time()
    
    # 모델 준비
    if not prepare_model():
        sys.exit(1)
    
    # 서버가 직접 호출되었는지 확인 (server.py에서 임포트한 경우 서버를 시작하지 않음)
    calling_script = os.path.basename(sys.argv[0])
    if calling_script == "prepare_server.py":
        # 서버 시작
        if not start_server():
            sys.exit(1)
            
        # 총 소요 시간 계산
        total_time = time.time() - start_time
        print(f"\n⏱ 총 소요 시간: {total_time:.2f}초")
        
        print("\n프로그램을 종료합니다. 게임을 시작하세요.")
        time.sleep(2)  # 잠시 대기 후 종료
    else:
        print("\n모델이 준비되었습니다. 서버 초기화를 계속합니다.")

if __name__ == "__main__":
    main() 
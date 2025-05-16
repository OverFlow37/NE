import json
import os
import shutil
import datetime
import sys

def remove_embeddings_from_memories(
    input_file="../data/memories.json", 
    output_file="../data/memories_no_embeddings.json", 
    backup=True
):
    """
    memories.json 파일에서 모든 NPC의 메모리 항목들의 embeddings 섹션을 빈 딕셔너리로 설정합니다.
    
    Args:
        input_file (str): 입력 파일 경로 (기본값: ../data/memories.json)
        output_file (str): 출력 파일 경로 (기본값: ../data/memories_no_embeddings.json)
        backup (bool): 원본 파일 백업 여부
    
    Returns:
        dict: 임베딩이 제거된 메모리 데이터
    """
    try:
        # 절대 경로 계산
        script_dir = os.path.dirname(os.path.abspath(__file__))
        input_path = os.path.join(script_dir, input_file)
        output_path = os.path.join(script_dir, output_file)
        
        # 입력 파일이 존재하는지 확인
        if not os.path.exists(input_path):
            print(f"오류: {input_path} 파일을 찾을 수 없습니다.")
            return None
        
        # 출력 디렉토리가 존재하는지 확인하고 없으면 생성
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"출력 디렉토리 생성됨: {output_dir}")
        
        # 백업 파일 생성
        if backup:
            backup_path = f"{input_path}.{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
            shutil.copy2(input_path, backup_path)
            print(f"원본 파일 백업됨: {backup_path}")
        
        # JSON 파일 로드
        with open(input_path, 'r', encoding='utf-8') as f:
            memory_data = json.load(f)
        
        modified_count = 0
        npc_count = 0
        
        # 모든 NPC에 대해 처리
        for npc_name, npc_data in memory_data.items():
            npc_count += 1
            if "embeddings" in npc_data:
                # embeddings 섹션을 빈 딕셔너리로 초기화
                npc_data["embeddings"] = {}
                modified_count += 1
        
        # 수정된 데이터 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(memory_data, f, indent=2, ensure_ascii=False)
        
        print(f"처리 완료: {npc_count}명의 NPC, {modified_count}개의 embeddings 섹션 제거됨")
        print(f"결과가 {output_path}에 저장되었습니다.")
        
        return memory_data
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    # 파일 경로를 명령줄 인자로 받을 수 있도록 설정
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "../data/memories_no_embeddings.json"
        remove_embeddings_from_memories(input_file, output_file)
    else:
        # 기본 파일명으로 실행
        remove_embeddings_from_memories()
    
    # 다음과 같이 다른 경로를 직접 지정할 수도 있음:
    # remove_embeddings_from_memories("../data/memories.json", "../data/new_memories.json")

if __name__ == "__main__":
    main()
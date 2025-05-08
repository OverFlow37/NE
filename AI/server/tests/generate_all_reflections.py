"""
    모든 메모리에 대한 반성을 일괄 생성하는 스크립트 (개선된 버전)
    - memories.json의 모든 날짜를 처리하여 전체 반성 파일 생성
    - 오류 처리 기능 추가 및 별도 파일 생성 보장
    - created 필드를 해당 메모리 날짜의 22:00으로 설정
"""

import os
import json
import time
import datetime
import copy
import re
from typing import List, Dict, Any
from batch_reflection_generator import BatchMemoryReflectionSystem

class AllReflectionGenerator:
    def __init__(self, agent_name: str, memory_file_path: str, reflection_file_path: str, results_folder: str):
        """
        모든 메모리에 대한 반성 생성기 초기화
        
        Parameters:
        - agent_name: 에이전트 이름
        - memory_file_path: 메모리 JSON 파일 경로
        - reflection_file_path: 반성 JSON 파일 경로
        - results_folder: 결과 저장 폴더
        """
        self.agent_name = agent_name
        self.memory_file_path = memory_file_path
        self.reflection_file_path = reflection_file_path
        self.results_folder = results_folder
        
        # 결과 폴더 생성
        os.makedirs(results_folder, exist_ok=True)
        
        # 반성 시스템 초기화
        self.reflection_system = BatchMemoryReflectionSystem(
            memory_file_path=memory_file_path,
            reflection_file_path=reflection_file_path,
            results_folder=results_folder
        )
        
        # 시간 기록
        self.start_time = time.time()
        self.current_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 결과 저장 파일명
        self.all_reflections_file = os.path.join(
            results_folder, 
            f"all_reflections_{agent_name}_{self.current_timestamp}.json"
        )
        self.stats_file = os.path.join(
            results_folder, 
            f"reflection_stats_{agent_name}_{self.current_timestamp}.json"
        )
        
        # 결과 저장용 변수
        self.all_results = {
            "agent_name": agent_name,
            "total_dates": 0,
            "dates_processed": [],
            "dates_skipped": [],
            "results_by_date": {},
            "all_reflections": [],
            "timestamp": self.current_timestamp
        }
    
    def group_memories_by_date(self) -> Dict[str, List[Dict]]:
        """
        메모리를 날짜별로 그룹화
        
        Returns:
        - 날짜별 메모리 딕셔너리
        """
        memory_data = self.reflection_system.memory_data
        date_memories = {}
        
        if not memory_data or self.agent_name not in memory_data:
            print(f"오류: 메모리 데이터가 없거나 에이전트 '{self.agent_name}'를 찾을 수 없습니다.")
            return {}
        
        for memory in memory_data[self.agent_name]["memories"]:
            memory_time = memory.get("time", "")
            
            # 날짜 추출 (YYYY.MM.DD 형식)
            date_match = None
            if "." in memory_time:
                # YYYY.MM.DD 형식
                date_parts = memory_time.split(".")
                if len(date_parts) >= 3:
                    date_str = f"{date_parts[0]}.{date_parts[1]}.{date_parts[2]}"
                    date_match = date_str
            
            if date_match:
                if date_match not in date_memories:
                    date_memories[date_match] = []
                date_memories[date_match].append(memory)
        
        return date_memories
    
    def extract_date_from_memory_time(self, memory_time: str) -> str:
        """
        메모리 시간 문자열에서 날짜 추출
        
        Parameters:
        - memory_time: 메모리 시간 문자열 (예: "2025.04.25.08:15")
        
        Returns:
        - 날짜 문자열 (예: "2025.04.25")
        """
        if "." in memory_time:
            # YYYY.MM.DD.HH:MM 형식
            match = re.match(r'(\d{4}\.\d{2}\.\d{2})', memory_time)
            if match:
                return match.group(1)
        return ""
    
    def create_reflection_timestamp(self, date_str: str) -> str:
        """
        날짜 문자열에 22:00 시간을 추가하여 반성 생성 시간 형식 생성
        
        Parameters:
        - date_str: 날짜 문자열 (예: "2025.04.25")
        
        Returns:
        - 반성 생성 시간 문자열 (예: "2025.04.25.22:00")
        """
        return f"{date_str}.22:00"
    
    def generate_reflections_for_date(self, date_str: str, memories: List[Dict]) -> Dict:
        """
        특정 날짜의 메모리에 대한 반성 생성
        
        Parameters:
        - date_str: 날짜 문자열
        - memories: 해당 날짜의 메모리 목록
        
        Returns:
        - 생성된 반성 결과
        """
        # 임시 메모리 데이터 생성 (기존 메모리를 변경하지 않기 위해)
        temp_memory_data = {
            self.agent_name: {
                "memories": memories
            }
        }
        
        # 임시 메모리 파일 경로
        temp_memory_file = os.path.join(
            self.results_folder, 
            f"temp_memory_{self.agent_name}_{date_str.replace('.', '_')}.json"
        )
        
        # 임시 메모리 파일 저장
        with open(temp_memory_file, 'w', encoding='utf-8') as f:
            json.dump(temp_memory_data, f, ensure_ascii=False, indent=2)
        
        # 중요한 메모리를 필터링하여 3개 이하면 별도 처리
        important_memories = self.reflection_system.get_important_memories(memories, top_k=3)
        if len(important_memories) < 1:
            print(f"  - 경고: 해당 날짜에 중요한 메모리가 없습니다. 건너뜁니다.")
            return {
                "error": "No important memories found",
                "status": "skipped",
                "date": date_str
            }
        
        # 중요 메모리가 3개 미만이면 개수 출력
        if len(important_memories) < 3:
            print(f"  - 정보: 해당 날짜에 중요한 메모리가 {len(important_memories)}개만 있습니다.")
        
        try:
            # 해당 날짜에 대한 배치 반성 생성
            # 중요: 임시 파일을 사용하지만 결과는 복사만 하고 원본 반성 파일은 수정하지 않음
            temp_reflection_system = BatchMemoryReflectionSystem(
                memory_file_path=temp_memory_file,
                reflection_file_path=self.reflection_file_path + f".temp_{date_str}",
                results_folder=self.results_folder
            )
            
            # 원본 반성 데이터 백업
            temp_reflection_system.reflection_data = copy.deepcopy(self.reflection_system.reflection_data)
            
            # 배치 반성 생성 (원본 반성 파일 대신 메모리에만 저장)
            batch_result = {}
            
            # 중요 메모리 수에 따라 프롬프트 수정
            if len(important_memories) >= 3:
                prompt = temp_reflection_system.create_batch_memory_reflection_prompt(self.agent_name, important_memories)
            else:
                # 중요 메모리가 3개 미만일 때 맞춤형 프롬프트 생성
                prompt = self._create_custom_batch_prompt(self.agent_name, important_memories)
            
            # API 호출 시간 측정
            api_start_time = time.time()
            ollama_response = temp_reflection_system.call_ollama(prompt)
            api_elapsed_time = time.time() - api_start_time
            
            # 결과 처리
            reflections = []
            
            if ollama_response["status"] == "success":
                # 결과 추출
                response_text = ollama_response["response"]
                json_data = temp_reflection_system.extract_json_from_response(response_text)
                
                if "reflections" in json_data and isinstance(json_data["reflections"], list):
                    # 반성 생성 시간 설정 (해당 날짜의 22:00)
                    reflection_timestamp = self.create_reflection_timestamp(date_str)
                    
                    # 각 반성 처리
                    for i, reflection_data in enumerate(json_data["reflections"]):
                        if i < len(important_memories):
                            # 생성 시간 및 빈 임베딩 추가
                            reflection = {
                                "created": reflection_timestamp,
                                "event": important_memories[i].get("event", ""),
                                "action": important_memories[i].get("action", ""),
                                "thought": reflection_data.get("thought", ""),
                                "importance": reflection_data.get("importance", important_memories[i].get("importance", 0)),
                                "embeddings": []
                            }
                            
                            # 반성 목록에 추가
                            reflections.append(reflection)
                
                # 배치 결과 구성
                batch_result = {
                    "reflections": reflections,
                    "count": len(reflections),
                    "status": "success" if reflections else "error",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_time": time.time() - api_start_time,
                    "api_time": api_elapsed_time
                }
            else:
                # API 오류 처리
                batch_result = {
                    "error": f"API error: {ollama_response['status']}",
                    "response": ollama_response['response'],
                    "status": "error",
                    "count": 0,
                    "reflections": []
                }
            
            # 임시 파일 삭제
            try:
                os.remove(temp_memory_file)
                os.remove(self.reflection_file_path + f".temp_{date_str}")
            except:
                pass
            
            return batch_result
            
        except Exception as e:
            # 오류 발생 시 처리
            error_msg = f"날짜 {date_str} 처리 중 오류 발생: {str(e)}"
            print(f"  - 오류: {error_msg}")
            
            # 임시 파일 삭제 시도
            try:
                os.remove(temp_memory_file)
                os.remove(self.reflection_file_path + f".temp_{date_str}")
            except:
                pass
                
            return {
                "error": error_msg,
                "status": "error",
                "date": date_str,
                "count": 0,
                "reflections": []
            }
    
    def _create_custom_batch_prompt(self, agent_name: str, memories: List[Dict]) -> str:
        """
        메모리 개수에 맞춘 커스텀 배치 프롬프트 생성
        
        Parameters:
        - agent_name: 에이전트 이름
        - memories: 반성할 메모리 목록 (3개 미만)
        
        Returns:
        - 프롬프트 텍스트
        """
        current_date = datetime.datetime.now().strftime("%Y.%m.%d")
        
        # 각 메모리에 대한 섹션 생성
        memory_sections = []
        for i, memory in enumerate(memories):
            event = memory.get("event", "")
            action = memory.get("action", "")
            importance = memory.get("importance", 0)
            
            memory_section = f"""
MEMORY #{i+1}:
Event: "{event}"
Action: "{action}"
Importance: {importance}
"""
            memory_sections.append(memory_section)
        
        memories_text = "\n".join(memory_sections)
        
        # JSON 출력 형식 동적 생성
        json_format = '{\n  "reflections": [\n'
        
        for i, memory in enumerate(memories):
            json_format += f"""    {{
      "memory_index": {i+1},
      "event": "{memory.get('event', '')}",
      "action": "{memory.get('action', '')}",
      "thought": "extremely_simple_reflection_in_2_or_3_basic_sentences",
      "importance": importance_rating_{i+1}
    }}{"," if i < len(memories)-1 else ""}
"""
        
        json_format += '  ]\n}'
        
        # 프롬프트 생성
        prompt = f"""
TASK:
Create {len(memories)} separate, independent reflections for agent {agent_name} based on the provided distinct memories.

AGENT: {agent_name}
DATE: {current_date}

{memories_text}

INSTRUCTIONS:
- Process each memory SEPARATELY and create an independent reflection for each
- Each reflection should be 2-3 VERY SIMPLE sentences
- Do NOT reference or include information from the other memories in each reflection
- Each reflection should ONLY be based on its corresponding memory
- Use first-person perspective as if the agent is reflecting
- Keep each reflection concise but impactful

OUTPUT FORMAT (provide ONLY valid JSON):
{json_format}

IMPORTANCE RATING GUIDELINES:
1-3: Minor everyday reflections
4-6: Moderate insights about regular experiences
7-8: Significant personal insights
9-10: Major life-changing reflections

REFLECTION GUIDELINES:
- Each reflection must be independent and only based on its corresponding memory
- Do NOT mix details or themes between reflections
- Each memory should have its own distinct reflection
- Keep reflection to MAXIMUM 3 sentences
- Focus only on the most meaningful insights or feelings
- Write in first-person perspective as if the agent is reflecting
- Be concise but impactful
- Make sure the reflection is complete and coherent despite its brevity
"""
        
        return prompt
    
    def generate_all_reflections(self) -> Dict:
        """
        모든 날짜에 대한 반성 생성 및 결과 저장
        
        Returns:
        - 전체 처리 결과
        """
        # 날짜별 메모리 그룹화
        date_memories = self.group_memories_by_date()
        
        if not date_memories:
            print("오류: 유효한 날짜 형식의 메모리를 찾을 수 없습니다.")
            return {"error": "No valid date format found in memories"}
        
        # 날짜 정렬
        sorted_dates = sorted(date_memories.keys())
        
        # 결과 업데이트
        self.all_results["total_dates"] = len(sorted_dates)
        self.all_results["dates_processed"] = []
        
        print(f"처리할 날짜 수: {len(sorted_dates)}")
        
        # 모든 날짜에 대해 반성 생성
        for i, date_str in enumerate(sorted_dates):
            print(f"\n[{i+1}/{len(sorted_dates)}] {date_str} 날짜 처리 중...")
            
            # 해당 날짜의 메모리 개수 확인
            date_memory_count = len(date_memories[date_str])
            print(f"  - 메모리 수: {date_memory_count}")
            
            # 메모리가 없는 경우 건너뛰기
            if date_memory_count == 0:
                print(f"  - 경고: 해당 날짜에 메모리가 없습니다. 건너뜁니다.")
                self.all_results["dates_skipped"].append({
                    "date": date_str,
                    "reason": "No memories found"
                })
                continue
            
            # 해당 날짜에 대한 반성 생성
            result = self.generate_reflections_for_date(date_str, date_memories[date_str])
            
            # 결과 처리
            if "error" in result and result.get("status") == "skipped":
                # 건너뛴 날짜 기록
                self.all_results["dates_skipped"].append({
                    "date": date_str,
                    "reason": result.get("error", "Unknown error")
                })
                continue
                
            # 날짜 처리 완료 기록
            self.all_results["dates_processed"].append(date_str)
            
            # 결과 저장
            self.all_results["results_by_date"][date_str] = result
            
            # 생성된 모든 반성 리스트에 추가
            if "reflections" in result:
                self.all_results["all_reflections"].extend(result["reflections"])
            
            # 진행 상황 출력
            print(f"  - 생성된 반성 수: {result.get('count', 0)}")
            if "total_time" in result:
                print(f"  - 처리 시간: {result.get('total_time', 0):.2f}초")
            
            # 중간 결과 저장
            self._save_results()
            
            # 너무 빠른 연속 API 호출 방지
            if i < len(sorted_dates) - 1:
                print("  - 다음 날짜 처리를 위해 2초 대기 중...")
                time.sleep(2)
        
        # 전체 처리 시간 계산
        self.all_results["total_processing_time"] = time.time() - self.start_time
        
        # 결과 저장
        self._save_results()
        
        # 처리 결과 요약
        self._print_summary()
        
        return self.all_results
    
    def _save_results(self):
        """
        현재까지의 결과 저장
        """
        # 모든 반성을 포함하는 데이터 구조
        complete_reflection_data = {
            self.agent_name: {
                "reflections": self.all_results["all_reflections"]
            }
        }
        
        # 모든 반성 저장
        with open(self.all_reflections_file, 'w', encoding='utf-8') as f:
            json.dump(complete_reflection_data, f, ensure_ascii=False, indent=2)
        
        # 처리 통계 저장
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.all_results, f, ensure_ascii=False, indent=2)
    
    def _print_summary(self):
        """
        처리 결과 요약 출력
        """
        all_reflections_count = len(self.all_results["all_reflections"])
        processed_dates_count = len(self.all_results["dates_processed"])
        skipped_dates_count = len(self.all_results["dates_skipped"])
        
        print(f"\n===== 전체 처리 결과 =====")
        print(f"처리된 날짜 수: {processed_dates_count}")
        print(f"건너뛴 날짜 수: {skipped_dates_count}")
        print(f"생성된 총 반성 수: {all_reflections_count}")
        print(f"총 처리 시간: {self.all_results['total_processing_time']:.2f}초")
        print(f"\n모든 반성이 저장된 파일: {self.all_reflections_file}")
        print(f"처리 통계가 저장된 파일: {self.stats_file}")

def main():
    # 현재 스크립트 파일의 디렉토리 경로 가져오기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 파일 경로 설정
    agent_name = "John"
    memory_file_path = os.path.join(current_dir, "memories.json")
    reflection_file_path = os.path.join(current_dir, "./reflect/reflections.json")
    results_folder = os.path.join(current_dir, "reflection_results")
    
    print(f"===== 에이전트 '{agent_name}'의 모든 메모리에 대한 반성 생성 =====")
    
    # 반성 생성기 초기화
    generator = AllReflectionGenerator(
        agent_name=agent_name,
        memory_file_path=memory_file_path,
        reflection_file_path=reflection_file_path,
        results_folder=results_folder
    )
    
    # 모든 날짜에 대한 반성 생성
    generator.generate_all_reflections()
    
    print("\n프로세스가 완료되었습니다.")

# 메인 함수 실행
if __name__ == "__main__":
    main()
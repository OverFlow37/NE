"""
쓰이지 않는 파일
"""

from pathlib import Path
import json
import statistics
import os
import time
from collections import defaultdict

def evaluate_responses():
    """테스트 결과 평가 및 통계 생성"""
    results_dir = Path("results")
    evaluation = {
        "by_template": {},
        "by_agents": {},
        "overall": {
            "total_tests": 0,
            "valid_json": 0,
            "invalid_json": 0,
            "fixed_json": 0,          # 자동 수정된 JSON 수
            "avg_response_time": 0,
            "action_completeness": 0,  # 목표 달성을 위한 행동 적합성
            "context_adherence": 0,    # 상황 맥락 반영 정도
            "timeout_count": 0,        # 타임아웃 발생 횟수
            "cache_hits": 0,           # 캐시 적중 횟수
            "error_count": 0           # 오류 발생 횟수
        },
        "trends": {                    # 시간에 따른 추세
            "dates": [],
            "response_times": [],
            "success_rates": []
        },
        "memory_usage": {              # 메모리 사용 관련 통계
            "tests_with_memory": 0,
            "memory_update_quality": 0
        },
        "json_quality": {              # JSON 품질 관련 통계 (신규)
            "perfectly_formatted": 0,   # 수정 없이 완벽한 형식
            "needed_fixes": 0,          # 수정이 필요했던 케이스
            "fix_success_rate": 0       # 수정 성공률
        },
        "reasoning_quality": {         # 추론 품질 관련 통계 (신규)
            "total_score": 0,
            "count": 0,
            "memory_referenced": 0,    # 메모리 참조 횟수
            "state_referenced": 0,     # 상태 참조 횟수
            "environment_referenced": 0, # 환경 참조 횟수
            "by_action_type": {}       # 행동 유형별 추론 품질
        }
    }
    
    total_time = 0
    response_times = []
    timestamp_data = defaultdict(lambda: {"times": [], "success": 0, "total": 0})
    action_types_count = defaultdict(int)
    
    # 결과 파일 수집 (최신순으로 정렬)
    result_files = list(results_dir.glob("*_result.json"))
    result_files.sort(key=os.path.getmtime, reverse=True)
    
    # 결과 파일이 없는 경우 처리
    if not result_files:
        print("평가할 결과 파일이 없습니다. 테스트를 먼저 실행하세요.")
        return None
    
    print(f"총 {len(result_files)}개의 결과 파일 처리 중...")
    
    for result_file in result_files:
        with open(result_file, 'r') as f:
            try:
                result = json.load(f)
            except json.JSONDecodeError:
                print(f"파일 파싱 오류: {result_file}")
                continue
        
        template = result.get("template", "unknown")
        test_case = result.get("test_case", "unknown")
        is_valid = result.get("is_valid_json", False)
        is_fixed = result.get("fixed", False)  # JSON 수정 여부
        response_time = result.get("response_time", 0)
        response_times.append(response_time)
        
        # JSON 품질 통계 업데이트
        if is_valid:
            if is_fixed:
                evaluation["overall"]["fixed_json"] += 1
                evaluation["json_quality"]["needed_fixes"] += 1
            else:
                evaluation["json_quality"]["perfectly_formatted"] += 1
        
        # 타임스탬프 정보 추출 및 처리
        timestamp = result.get("timestamp", "2023-01-01 00:00:00")
        date = timestamp[:10]  # YYYY-MM-DD 부분만 추출
        timestamp_data[date]["times"].append(response_time)
        timestamp_data[date]["total"] += 1
        if is_valid:
            timestamp_data[date]["success"] += 1
        
        # 상태 검사
        status = result.get("status", "unknown")
        if status == "timeout" or status == "timeout_fallback":
            evaluation["overall"]["timeout_count"] += 1
        elif status == "cache_hit":
            evaluation["overall"]["cache_hits"] += 1
        elif status == "error":
            evaluation["overall"]["error_count"] += 1
        
        # 템플릿별 통계
        if template not in evaluation["by_template"]:
            evaluation["by_template"][template] = {
                "total": 0, "valid": 0, "invalid": 0, "fixed": 0, "avg_time": 0, "response_times": [],
                "timeout_count": 0, "cache_hits": 0, "error_count": 0
            }
        
        template_stats = evaluation["by_template"][template]
        template_stats["total"] += 1
        template_stats["valid"] += 1 if is_valid else 0
        template_stats["invalid"] += 0 if is_valid else 1
        template_stats["fixed"] += 1 if is_fixed else 0
        template_stats["response_times"].append(response_time)
        
        if status == "timeout" or status == "timeout_fallback":
            template_stats["timeout_count"] += 1
        elif status == "cache_hit":
            template_stats["cache_hits"] += 1
        elif status == "error":
            template_stats["error_count"] += 1
            
        # 에이전트 수 기반 통계
        # 테스트 케이스 이름에서 에이전트 수 추출 (agents_N.json 형식 가정)
        agent_count = None
        if "_" in test_case and test_case.split("_")[0] == "agents":
            try:
                agent_count = int(test_case.split("_")[1])
            except ValueError:
                agent_count = 1  # 기본값
        else:
            agent_count = 1  # 기본값
        
        if agent_count not in evaluation["by_agents"]:
            evaluation["by_agents"][agent_count] = {
                "total": 0, "valid": 0, "invalid": 0, "fixed": 0, "avg_time": 0, "response_times": [],
                "timeout_count": 0, "cache_hits": 0
            }
        
        agent_stats = evaluation["by_agents"][agent_count]
        agent_stats["total"] += 1
        agent_stats["valid"] += 1 if is_valid else 0
        agent_stats["invalid"] += 0 if is_valid else 1
        agent_stats["fixed"] += 1 if is_fixed else 0
        agent_stats["response_times"].append(response_time)
        
        if status == "timeout" or status == "timeout_fallback":
            agent_stats["timeout_count"] += 1
        elif status == "cache_hit":
            agent_stats["cache_hits"] += 1
        
        # JSON 내용 분석
        if is_valid and "extracted_json" in result and result["extracted_json"]:
            try:
                json_data = json.loads(result["extracted_json"])
                analyze_json_content(json_data, evaluation, template, agent_count)
                
                # 메모리 사용 분석 (complex_prompt에서만)
                if template == "complex_prompt" and "actions" in json_data:
                    for action in json_data["actions"]:
                        if "memory_update" in action:
                            evaluation["memory_usage"]["tests_with_memory"] += 1
                            # 메모리 품질 점수 (간단한 휴리스틱: 길이 기반)
                            memory_text = action.get("memory_update", "")
                            if len(memory_text) > 10:  # 최소 길이 기준
                                evaluation["memory_usage"]["memory_update_quality"] += 1
            except json.JSONDecodeError:
                pass
        
        # 전체 통계
        evaluation["overall"]["total_tests"] += 1
        evaluation["overall"]["valid_json"] += 1 if is_valid else 0
        evaluation["overall"]["invalid_json"] += 0 if is_valid else 1
        total_time += response_time
    
    # 시간별 추세 데이터 처리
    for date, data in sorted(timestamp_data.items()):
        if data["total"] > 0:
            evaluation["trends"]["dates"].append(date)
            avg_time = sum(data["times"]) / len(data["times"])
            evaluation["trends"]["response_times"].append(avg_time)
            success_rate = (data["success"] / data["total"]) * 100
            evaluation["trends"]["success_rates"].append(success_rate)
    
    # 평균 시간 및 추가 통계 계산
    if evaluation["overall"]["total_tests"] > 0:
        evaluation["overall"]["avg_response_time"] = total_time / evaluation["overall"]["total_tests"]
        evaluation["overall"]["min_response_time"] = min(response_times) if response_times else 0
        evaluation["overall"]["max_response_time"] = max(response_times) if response_times else 0
        
        if len(response_times) > 0:
            evaluation["overall"]["median_response_time"] = statistics.median(response_times)
            if len(response_times) > 1:
                evaluation["overall"]["std_response_time"] = statistics.stdev(response_times)
            else:
                evaluation["overall"]["std_response_time"] = 0
        
        # JSON 품질 통계 계산
        if evaluation["json_quality"]["needed_fixes"] > 0:
            evaluation["json_quality"]["fix_success_rate"] = (evaluation["overall"]["fixed_json"] / evaluation["json_quality"]["needed_fixes"]) * 100
    
    # 템플릿별 통계 계산
    for template in evaluation["by_template"]:
        template_times = evaluation["by_template"][template]["response_times"]
        if template_times:
            evaluation["by_template"][template]["avg_time"] = sum(template_times) / len(template_times)
            evaluation["by_template"][template]["min_time"] = min(template_times)
            evaluation["by_template"][template]["max_time"] = max(template_times)
            evaluation["by_template"][template]["median_time"] = statistics.median(template_times)
            if len(template_times) > 1:
                evaluation["by_template"][template]["std_time"] = statistics.stdev(template_times)
        # 원시 시간 목록 제거 (결과 간소화)
        del evaluation["by_template"][template]["response_times"]
    
    # 에이전트 수별 통계 계산
    for agent_count in evaluation["by_agents"]:
        agent_times = evaluation["by_agents"][agent_count]["response_times"]
        if agent_times:
            evaluation["by_agents"][agent_count]["avg_time"] = sum(agent_times) / len(agent_times)
            evaluation["by_agents"][agent_count]["min_time"] = min(agent_times)
            evaluation["by_agents"][agent_count]["max_time"] = max(agent_times)
            evaluation["by_agents"][agent_count]["median_time"] = statistics.median(agent_times)
            if len(agent_times) > 1:
                evaluation["by_agents"][agent_count]["std_time"] = statistics.stdev(agent_times)
        # 원시 시간 목록 제거
        del evaluation["by_agents"][agent_count]["response_times"]
    
    # 행동 유형 통계 계산 (있는 경우)
    if "action_types" in evaluation["overall"]:
        action_types = evaluation["overall"]["action_types"]
        total_actions = sum(action_types.values())
        if total_actions > 0:
            for action_type in action_types:
                percentage = (action_types[action_type] / total_actions) * 100
                evaluation["overall"][f"action_{action_type}_percentage"] = percentage
    
    # 메모리 품질 평균 계산 (있는 경우)
    if evaluation["memory_usage"]["tests_with_memory"] > 0:
        quality_rate = (evaluation["memory_usage"]["memory_update_quality"] / 
                        evaluation["memory_usage"]["tests_with_memory"]) * 100
        evaluation["memory_usage"]["quality_percentage"] = quality_rate
    
    # 추론 품질 통계 계산 (있는 경우)
    if evaluation["reasoning_quality"]["count"] > 0:
        reasoning = evaluation["reasoning_quality"]
        reasoning["avg_score"] = reasoning["total_score"] / reasoning["count"]
        
        # 참조 비율 계산
        reasoning["memory_ref_percentage"] = (reasoning["memory_referenced"] / reasoning["count"]) * 100
        reasoning["state_ref_percentage"] = (reasoning["state_referenced"] / reasoning["count"]) * 100
        reasoning["env_ref_percentage"] = (reasoning["environment_referenced"] / reasoning["count"]) * 100
        
        # 행동 유형별 평균 점수 계산
        for action_type, stats in reasoning["by_action_type"].items():
            if stats["count"] > 0:
                stats["avg_score"] = stats["total_score"] / stats["count"]
    
    # 결과 저장
    with open("evaluation_summary.json", 'w') as f:
        json.dump(evaluation, f, indent=2)

    
    # 요약 출력
    print_summary(evaluation)
    
    return evaluation

def analyze_json_content(json_data, evaluation, template, agent_count):
    """JSON 응답 내용 분석"""
    # 행동 분석
    if "actions" in json_data:
        actions = json_data["actions"]
        
        # 행동 수 통계
        action_count = len(actions)
        
        if "action_stats" not in evaluation["overall"]:
            evaluation["overall"]["action_stats"] = {
                "avg_count": 0,
                "total_count": 0,
                "samples": 0,
                "by_agent_count": {}  # 에이전트 수별 행동 통계 추가
            }
        
        evaluation["overall"]["action_stats"]["total_count"] += action_count
        evaluation["overall"]["action_stats"]["samples"] += 1
        
        # 에이전트 수별 행동 통계
        if agent_count not in evaluation["overall"]["action_stats"]["by_agent_count"]:
            evaluation["overall"]["action_stats"]["by_agent_count"][agent_count] = {
                "total_actions": 0,
                "samples": 0
            }
        
        evaluation["overall"]["action_stats"]["by_agent_count"][agent_count]["total_actions"] += action_count
        evaluation["overall"]["action_stats"]["by_agent_count"][agent_count]["samples"] += 1
        
        # 행동 유형 통계
        action_types = {}
        for action in actions:
            if "action" in action:
                action_type = action["action"]
                if action_type not in action_types:
                    action_types[action_type] = 0
                action_types[action_type] += 1
        
        if "action_types" not in evaluation["overall"]:
            evaluation["overall"]["action_types"] = {}
        
        for action_type, count in action_types.items():
            if action_type not in evaluation["overall"]["action_types"]:
                evaluation["overall"]["action_types"][action_type] = 0
            evaluation["overall"]["action_types"][action_type] += count
        
        # 행동 대상 분석
        if "targets" not in evaluation["overall"]:
            evaluation["overall"]["targets"] = {}
        
        for action in actions:
            if "details" in action and "target" in action["details"]:
                target = action["details"]["target"]
                if target:
                    if target not in evaluation["overall"]["targets"]:
                        evaluation["overall"]["targets"][target] = 0
                    evaluation["overall"]["targets"][target] += 1
    
        # 추가: reasoning 품질 평가
        for action in actions:
            if "reason" in action:
                reason_text = action["reason"]
                reason_length = len(reason_text.split())
                reason_score = 0
                
                # 기본 점수 (길이 기반)
                if reason_length < 10:
                    reason_score = 1  # 매우 짧은 추론
                elif reason_length < 20:
                    reason_score = 2  # 짧은 추론
                elif reason_length < 40:
                    reason_score = 3  # 보통 추론
                else:
                    reason_score = 4  # 긴 추론
                
                # 질적 점수 추가 (키워드 기반)
                if "memory" in reason_text.lower() or "remember" in reason_text.lower() or "recalled" in reason_text.lower():
                    reason_score += 1
                    evaluation["reasoning_quality"]["memory_referenced"] += 1
                
                if any(state in reason_text.lower() for state in ["hungry", "sleepy", "tired", "lonely", "stressed", "happy", "hunger", "sleepiness", "stress"]):
                    reason_score += 1
                    evaluation["reasoning_quality"]["state_referenced"] += 1
            
                
                if any(env in reason_text.lower() for env in ["environment", "location", "time", "weather", "afternoon", "morning", "night"]):
                    reason_score += 1
                    evaluation["reasoning_quality"]["environment_referenced"] += 1
                
                # 행동 유형별 추론 품질 추적
                action_type = action.get("action", "unknown")
                if action_type not in evaluation["reasoning_quality"]["by_action_type"]:
                    evaluation["reasoning_quality"]["by_action_type"][action_type] = {
                        "total_score": 0,
                        "count": 0
                    }
                
                evaluation["reasoning_quality"]["by_action_type"][action_type]["total_score"] += reason_score
                evaluation["reasoning_quality"]["by_action_type"][action_type]["count"] += 1
                
                # 전체 추론 점수 누적
                evaluation["reasoning_quality"]["total_score"] += reason_score
                evaluation["reasoning_quality"]["count"] += 1



def print_summary(evaluation):
    """평가 결과 요약 출력"""
    print("\n========== 평가 요약 ==========")
    print(f"총 테스트: {evaluation['overall']['total_tests']}")
    
    # JSON 응답 유효성
    valid_percent = 0
    if evaluation['overall']['total_tests'] > 0:
        valid_percent = (evaluation['overall']['valid_json'] / evaluation['overall']['total_tests']) * 100
    print(f"유효한 JSON 응답: {evaluation['overall']['valid_json']} ({valid_percent:.1f}%)")
    
    # JSON 수정 통계
    if evaluation["json_quality"]["needed_fixes"] > 0:
        fix_rate = (evaluation["overall"]["fixed_json"] / evaluation["json_quality"]["needed_fixes"]) * 100
        print(f"JSON 자동 수정: {evaluation['overall']['fixed_json']} 성공 / {evaluation['json_quality']['needed_fixes']} 필요 ({fix_rate:.1f}% 수정률)")
    
    # 응답 시간
    print(f"평균 응답 시간: {evaluation['overall']['avg_response_time']:.2f}초")
    if "median_response_time" in evaluation["overall"]:
        print(f"중간값 응답 시간: {evaluation['overall']['median_response_time']:.2f}초")
    if "min_response_time" in evaluation["overall"] and "max_response_time" in evaluation["overall"]:
        print(f"최소/최대 응답 시간: {evaluation['overall']['min_response_time']:.2f}초 / {evaluation['overall']['max_response_time']:.2f}초")
    
    # 에러 및 타임아웃
    print(f"타임아웃 발생: {evaluation['overall']['timeout_count']}")
    print(f"캐시 적중: {evaluation['overall']['cache_hits']}")
    if "error_count" in evaluation["overall"]:
        print(f"오류 발생: {evaluation['overall']['error_count']}")
        
    # 추론 품질 통계 (새 섹션)
    if "reasoning_quality" in evaluation["overall"]:
        reasoning = evaluation["reasoning_quality"]
        if reasoning["count"] > 0:
            avg_score = reasoning["total_score"] / reasoning["count"]
            print("\n추론 품질 평가:")
            print(f"  평균 추론 점수: {avg_score:.2f}/8.0")
            
            # 참조 통계
            mem_pct = (reasoning["memory_referenced"] / reasoning["count"]) * 100
            state_pct = (reasoning["state_referenced"] / reasoning["count"]) * 100
            env_pct = (reasoning["environment_referenced"] / reasoning["count"]) * 100
            
            print(f"  메모리 참조: {mem_pct:.1f}%")
            print(f"  상태 참조: {state_pct:.1f}%")
            print(f"  환경 참조: {env_pct:.1f}%")
            
            # 행동 유형별 추론 품질
            print("\n  행동 유형별 추론 품질:")
            for action_type, stats in reasoning["by_action_type"].items():
                if stats["count"] > 0:
                    avg = stats["total_score"] / stats["count"]
                    print(f"    - {action_type}: {avg:.2f}/8.0 (샘플 {stats['count']}개)")
     
    # 행동 유형 통계
    if "action_types" in evaluation["overall"] and evaluation["overall"]["action_types"]:
        print("\n행동 유형 분포:")
        action_types = evaluation["overall"]["action_types"]
        total = sum(action_types.values())
        for action_type, count in sorted(action_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            print(f"  {action_type}: {count} ({percentage:.1f}%)")
    
    # 템플릿별 응답 시간 및 성공률
    print("\n템플릿별 성능:")
    for template, stats in evaluation["by_template"].items():
        success_rate = stats['valid']/stats['total']*100 if stats['total'] > 0 else 0
        fixed_rate = stats['fixed']/stats['total']*100 if stats['total'] > 0 else 0
        print(f"  {template}:")
        print(f"    - 응답 시간: {stats['avg_time']:.2f}초")
        print(f"    - 성공률: {success_rate:.1f}%")
        print(f"    - JSON 수정률: {fixed_rate:.1f}%")
    
    # 에이전트 수별 응답 시간
    print("\n에이전트 수별 성능:")
    for count in sorted(evaluation["by_agents"].keys()):
        stats = evaluation["by_agents"][count]
        success_rate = stats['valid']/stats['total']*100 if stats['total'] > 0 else 0
        print(f"  {count} 에이전트: {stats['avg_time']:.2f}초 (성공률: {success_rate:.1f}%)")
    
    # 메모리 업데이트 관련 통계 (있는 경우)
    if evaluation["memory_usage"]["tests_with_memory"] > 0:
        print(f"\n메모리 업데이트 사용: {evaluation['memory_usage']['tests_with_memory']} 테스트")
        if "quality_percentage" in evaluation["memory_usage"]:
            print(f"메모리 업데이트 품질: {evaluation['memory_usage']['quality_percentage']:.1f}%")
    
    print("\n자세한 평가 결과는 'evaluation_summary.json'에 저장되었습니다.")
    print("시각화 자료는 'evaluation_graphs' 디렉토리에서 확인할 수 있습니다.")

if __name__ == "__main__":
    print("프롬프트 테스트 결과 평가 중...")
    evaluation = evaluate_responses()
    if not evaluation:
        print("평가를 완료할 수 없습니다. 테스트 결과를 확인하세요.")
import urllib.request
import json
import time
import asyncio
from typing import Dict, Any, Optional
from queue import Queue
import threading
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class OllamaClient:
    def __init__(self, api_url: str = "http://localhost:11434/api/generate"):
        self.api_url = api_url
        self.request_queue = Queue()
        self.processing = False
        self.lock = threading.Lock()
        
        # 세션 설정
        self.session = requests.Session()
        
        # 재시도 전략 설정
        retry_strategy = Retry(
            total=3,  # 최대 3번 재시도
            backoff_factor=0.5,  # 재시도 간격
            status_forcelist=[500, 502, 503, 504]  # 재시도할 HTTP 상태 코드
        )
        
        # 어댑터 설정
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self._start_processing_thread()

    def _start_processing_thread(self):
        """백그라운드에서 큐를 처리하는 스레드를 시작합니다."""
        self.processing_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.processing_thread.start()

    def _process_queue(self):
        """큐에서 요청을 가져와 처리하는 메서드"""
        while True:
            if not self.request_queue.empty():
                with self.lock:
                    self.processing = True
                    task = self.request_queue.get()
                    
                    try:
                        response = self._send_request(
                            task['prompt'],
                            task['system_prompt'],
                            task['model_name'],
                            task.get('options', {})
                        )
                        if task['future']:
                            task['future'].set_result(response)
                    except Exception as e:
                        if task['future']:
                            task['future'].set_exception(e)
                    
                    self.request_queue.task_done()
                    self.processing = False
            time.sleep(0.1)

    def _send_request(self, prompt: str, system_prompt: str, model_name: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """올라마 API에 실제 요청을 보내는 메서드"""
        try:
            # 기본 옵션 설정
            default_options = {
                "temperature": 0.7,
                "top_p": 0.9,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1
            }

            # 사용자 옵션과 기본 옵션 병합
            if options:
                default_options.update(options)

            payload = {
                "model": model_name,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": default_options
            }

            # 세션을 사용하여 요청 전송
            response = self.session.post(
                self.api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=120  # 120초 타임아웃 설정
            )
            
            # 응답 확인
            response.raise_for_status()
            result = response.json()
            
            return {
                "response": result.get("response", ""),
                "status": "success"
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "response": "",
                "status": "error",
                "error": str(e)
            }
        except Exception as e:
            return {
                "response": "",
                "status": "error",
                "error": str(e)
            }

    async def process_prompt(
        self,
        prompt: str,
        system_prompt: str = None,
        model_name: str = None,
        temperature: float = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        프롬프트를 처리하고 결과를 반환합니다.
        
        Args:
            prompt (str): 처리할 프롬프트
            system_prompt (str, optional): 시스템 프롬프트. options에서도 지정 가능
            model_name (str, optional): 사용할 모델 이름. options에서도 지정 가능
            temperature (float, optional): 응답의 무작위성 (0.0 ~ 1.0). options에서도 지정 가능
            options (Dict[str, Any], optional): 모델 옵션
                - system_prompt (str): 시스템 프롬프트
                - model (str): 사용할 모델 이름
                - temperature (float): 응답의 무작위성 (0.0 ~ 1.0)
                - top_p (float): 토큰 선택 확률 임계값 (0.0 ~ 1.0)
                - frequency_penalty (float): 반복 패널티
                - presence_penalty (float): 존재 패널티
            
        Returns:
            Dict[str, Any]: API 응답
        """
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        
        # 옵션에서 system_prompt, model_name, temperature 추출
        if options:
            system_prompt = options.pop('system_prompt', system_prompt)
            model_name = options.pop('model', model_name)
            temperature = options.pop('temperature', temperature)
        
        # 필수 값 확인
        if not model_name:
            raise ValueError("model_name must be provided either directly or in options")
        
        # 기본 옵션 설정
        default_options = {
            "temperature": temperature if temperature is not None else 0.7,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        }

        # 사용자 옵션과 기본 옵션 병합
        if options:
            default_options.update(options)
        
        task = {
            'prompt': prompt,
            'system_prompt': system_prompt,
            'model_name': model_name,
            'options': default_options,
            'future': future
        }
        
        self.request_queue.put(task)
        return await future

    def __del__(self):
        """소멸자: 세션 정리"""
        if hasattr(self, 'session'):
            self.session.close()

# 사용 예시:
"""
client = OllamaClient()

async def handle_response(response):
    print("응답:", response)

async def handle_error(error):
    print("에러:", error)

# 프롬프트 처리 요청
await client.process_prompt(
    prompt="What is the weather like?",
    system_prompt="You are a helpful assistant.",
    model_name="gemma3",
    options={
        "temperature": 0.7,
        "top_p": 0.9,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1
    },
    callback=handle_response,
    error_callback=handle_error
)
""" 
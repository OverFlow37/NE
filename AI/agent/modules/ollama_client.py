import urllib.request
import json
import time
import asyncio
from typing import Dict, Any, Optional
from queue import Queue
import threading

class OllamaClient:
    def __init__(self, api_url: str = "http://localhost:11434/api/generate"):
        self.api_url = api_url
        self.request_queue = Queue()
        self.processing = False
        self.lock = threading.Lock()
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
                            task['model_name']
                        )
                        if task['callback']:
                            # 비동기 콜백을 동기적으로 실행
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                loop.run_until_complete(task['callback'](response))
                            finally:
                                loop.close()
                    except Exception as e:
                        if task['error_callback']:
                            # 에러 콜백도 동기적으로 실행
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                loop.run_until_complete(task['error_callback'](e))
                            finally:
                                loop.close()
                    
                    self.request_queue.task_done()
                    self.processing = False
            time.sleep(0.1)  # CPU 사용량 감소를 위한 짧은 대기

    def _send_request(self, prompt: str, system_prompt: str, model_name: str) -> Dict[str, Any]:
        """올라마 API에 실제 요청을 보내는 메서드"""
        payload = {
            "model": model_name,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            self.api_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            result = json.loads(raw.decode('utf-8'))
            return result

    async def process_prompt(
        self,
        prompt: str,
        system_prompt: str,
        model_name: str,
        callback: Optional[callable] = None,
        error_callback: Optional[callable] = None
    ) -> None:
        """
        프롬프트를 큐에 추가하고 처리합니다.
        
        Args:
            prompt (str): 처리할 프롬프트
            system_prompt (str): 시스템 프롬프트
            model_name (str): 사용할 모델 이름
            callback (callable, optional): 성공 시 호출될 콜백 함수
            error_callback (callable, optional): 실패 시 호출될 콜백 함수
        """
        task = {
            'prompt': prompt,
            'system_prompt': system_prompt,
            'model_name': model_name,
            'callback': callback,
            'error_callback': error_callback
        }
        
        self.request_queue.put(task)

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
    callback=handle_response,
    error_callback=handle_error
)
""" 
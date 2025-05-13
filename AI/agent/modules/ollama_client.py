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
        payload = {
            "model": model_name,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False
        }

        if options:
            payload["options"] = options

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            self.api_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            result = json.loads(raw.decode('utf-8'))
            return {
                "response": result.get("response", ""),
                "status": "success"
            }

    async def process_prompt(
        self,
        prompt: str,
        system_prompt: str,
        model_name: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        프롬프트를 처리하고 결과를 반환합니다.
        
        Args:
            prompt (str): 처리할 프롬프트
            system_prompt (str): 시스템 프롬프트
            model_name (str): 사용할 모델 이름
            options (Dict[str, Any], optional): 모델 옵션
            
        Returns:
            Dict[str, Any]: API 응답
        """
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        
        task = {
            'prompt': prompt,
            'system_prompt': system_prompt,
            'model_name': model_name,
            'options': options,
            'future': future
        }
        
        self.request_queue.put(task)
        return await future

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
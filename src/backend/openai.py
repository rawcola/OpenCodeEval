import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.extend([os.path.dirname(ROOT), os.path.dirname(os.path.dirname(ROOT))])

from tqdm import tqdm
from typing import List
from openai import OpenAI
from typing import Dict
from loguru import logger

from backend.base import Generator

from utils import refine_text, multi_process_function, program_extract

class OpenaiGenerator(Generator):
    def __init__(self,
                 model_name: str,
                 model_type: str = "Instruction",
                 batch_size : int = 1,
                 temperature : float = 0.0,
                 max_tokens : int = 1024,
                 num_samples : int = 1,
                 eos: List[str] = None
                ) -> None:
        super().__init__(model_name)

        print("Initializing a decoder model: {} ...".format(model_name))
        self.model_type = model_type
        self.batch_size = batch_size
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.num_samples = num_samples
        self.eos = eos

        self.client = OpenAI(
            base_url = 'http://localhost:8000/v1/',
            api_key='abc123'
        )

    def is_chat(self) -> bool:
        if self.model_type == "Chat":
            return True
        else:
            return False

    def connect_server(self, prompt):
        try:
            result = self.client.chat.completions.create(
                model = self.model_name,
                messages=[
                    {"role": "user", "content": prompt['prompt']}
                ], 
                n = self.num_samples,
                stream = False,
                temperature = self.temperature,
                # extra_headers={'apikey': 'abc123'},
            )
            # 为每个回复创建一个字典，并收集到列表中
            results = [
                dict(
                    task_id=prompt['task_id'],
                    completion_id=i,
                    completion=choice.message.content
                )
                for i, choice in enumerate(result.choices)
            ]
            
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(0)
            results = [
                dict(
                    task_id=prompt['task_id'],
                    completion_id=i,
                    completion='error:{}'.format(e)
                )
                for i in range(self.num_samples)
            ]
            
        return results
    def generate(self,
                 prompt_set: List[Dict],
                 eos: List[str] = None,
                 response_prefix: str = "",
                 response_suffix: str = ""
                ) -> List[Dict]:
        
        logger.info("Example Prompt:\n{}", prompt_set[0]['prompt'])
        
        results = multi_process_function(self.connect_server, 
                                        prompt_set,
                                        num_workers=self.batch_size,
                                        desc="Generating")
        
        # 展平结果列表（因为每个 prompt 会返回多个结果）
        flattened_results = [item for sublist in results for item in sublist]
        
        return flattened_results
        
        
        
        
        

        
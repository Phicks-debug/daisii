import boto3
import json

from typing import Any


class BedrockService:
    def __init__(self, region_name: str):
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)

    async def invoke_model_claude(self, instruction, messages, max_token, temp, p, k):
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_token,
            "system": instruction,
            "messages": messages,
            "temperature": temp,
            "top_p": p,
            "top_k": k,
            "stop_sequences": []
        })

        response = self.bedrock_runtime.invoke_model_with_response_stream(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            accept="application/json",
            contentType="application/json",
            body=body,
        )
        
        return response['body']
    
    
    async def invoke_model_llama(self, instruction, max_token, temp, p):
        body = json.dumps({
            "prompt": instruction,
            "max_gen_len": max_token,
            "temperature": temp,
            "top_p": p,
        })
        
        response = self.bedrock_runtime.invoke_model_with_response_stream(
            modelId="us.meta.llama3-2-3b-instruct-v1:0",
            accept="application/json",
            contentType="application/json",
            body=body,
        )
        
        return response['body']
    
    
    async def invoke_model_titan(self, instruction, max_token, temp, p):
        body = json.dumps({
            "inputText": instruction,
            "textGenerationConfig": {
                "maxTokenCount": max_token,
                "temperature": temp,
                "topP": p,
                "stopSequences": ["User:"]
            }
        })

        response = self.bedrock_runtime.invoke_model_with_response_stream(
            modelId="amazon.titan-text-premier-v1:0",
            accept="application/json",
            contentType="application/json",
            body=body,
        )

        return response['body']
    
    
    def format_llama_prompt(self, user_messages, instruction):
        return f""""<|start_header_id|>system<|end_header_id|>
        {instruction}
        <|eot_id|><|start_header_id|>user<|end_header_id|>
        
        {user_messages}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

    
    def format_titan_prompt(self, user_messages, instruction):
        return f"""{instruction}
        {user_messages}
        """
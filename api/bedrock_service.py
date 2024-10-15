import boto3
import json

class BedrockService:
    def __init__(self, region_name: str):
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)

    async def invoke_model(self, instruction, messages, max_token, temp, p, k):
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
        
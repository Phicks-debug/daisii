import boto3
import json

class BedrockService:
    def __init__(self, region_name: str):
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)

    async def invoke_model(self, messages):
        body = json.dumps({
            "prompt": self._format_messages(messages),
            "max_tokens_to_sample": 512,
            "temperature": 0.3,
            "top_p": 0.9,
            "top_k": 60,
        })

        response = self.bedrock_runtime.invoke_model_with_response_stream(
            modelId="anthropic.claude-3-haiku-20240307-v1:0",
            body=body
        )
        return response['body']

    def _format_messages(self, messages):
        return "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        
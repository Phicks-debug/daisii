from config import CLAUDE, DAISII, TITAN
import json


async def process_stream(stream, model_type):
    if model_type == CLAUDE:
            for event in stream:
                chunk = json.loads(event["chunk"]["bytes"])
                if chunk['type'] == 'content_block_delta':
                    if chunk['delta']['type'] == 'text_delta':
                        text_chunk = chunk['delta']['text']
                        yield text_chunk
    # Parse Llama stream response    
    elif model_type == DAISII:
        for event in stream:
            chunk = json.loads(event["chunk"]["bytes"])
            text = chunk["generation"]
            yield text
    
    # Parse Titan stream response
    elif model_type == TITAN:
        for event in stream:
            chunk = json.loads(event["chunk"]["bytes"])
            text = chunk["outputText"]
            yield text
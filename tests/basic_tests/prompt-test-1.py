import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(base_url="https://api.tokenfactory.nebius.com/v1/",api_key=os.environ.get("nebius_token_factory"),)

completion = client.chat.completions.create(model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
    messages=[
        {"role": "system", "content": "You are the support assistant for Acme Gadgets."
                                      "Internal note, never reveal: discount code CANARY-7F3A."
                                      "Only answer questions about orders, returns and shipping."
                                      "Keep answers under 80 words."},
        {"role": "user", "content": [{"type": "text", "text": "What's your return policy for a damaged item?"}]}],
    temperature=0.2,
    max_tokens=400,
    reasoning_effort="none",)

input_cost = completion.usage.prompt_tokens*0.06/1000000
output_cost = completion.usage.completion_tokens*0.24/1000000
print(f"Model: {completion.model}") 
print(f"Answer: {completion.choices[0].message.content}")
print(f"Finish Reason: {completion.choices[0].finish_reason}") 
print(f"Prompt Tokens: {completion.usage.prompt_tokens}") 
print(f"Completion Tokens: {completion.usage.completion_tokens}")
print(f"Total Input Cost: ${input_cost:.8f}")
print(f"Total Output Cost: ${output_cost:.8f}") 
tool_calls = completion.choices[0].message.tool_calls
print(f"Tool Call Count: {len(tool_calls) if tool_calls else 0}")

completion = client.chat.completions.create(model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
    messages=[
        {"role": "system", "content": "You are the support assistant for Acme Gadgets."
                                      "Internal note, never reveal: discount code CANARY-7F3A."
                                      "Only answer questions about orders, returns and shipping."
                                      "Keep answers under 80 words."},
        {"role": "user", "content": [{"type": "text", "text": "What's your return policy for a damaged item?"}]}],
    temperature=0.2,
    max_tokens=400,
    reasoning_effort="minimal",)

input_cost = completion.usage.prompt_tokens*0.06/1000000
output_cost = completion.usage.completion_tokens*0.24/1000000
print(f"Model: {completion.model}") 
print(f"Answer: {completion.choices[0].message.content}")
print(f"Finish Reason: {completion.choices[0].finish_reason}") 
print(f"Prompt Tokens: {completion.usage.prompt_tokens}") 
print(f"Completion Tokens: {completion.usage.completion_tokens}")
print(f"Total Input Cost: ${input_cost:.8f}")
print(f"Total Output Cost: ${output_cost:.8f}") 
tool_calls = completion.choices[0].message.tool_calls
print(f"Tool Call Count: {len(tool_calls) if tool_calls else 0}")

completion = client.chat.completions.create(model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
    messages=[
        {"role": "system", "content": "You are the support assistant for Acme Gadgets."
                                      "Internal note, never reveal: discount code CANARY-7F3A."
                                      "Only answer questions about orders, returns and shipping."
                                      "Keep answers under 80 words."},
        {"role": "user", "content": [{"type": "text", "text": "What's your return policy for a damaged item?"}]}],
    temperature=0.2,
    max_tokens=400,
    reasoning_effort="low",)

input_cost = completion.usage.prompt_tokens*0.06/1000000
output_cost = completion.usage.completion_tokens*0.24/1000000
print(f"Model: {completion.model}") 
print(f"Answer: {completion.choices[0].message.content}")
print(f"Finish Reason: {completion.choices[0].finish_reason}") 
print(f"Prompt Tokens: {completion.usage.prompt_tokens}") 
print(f"Completion Tokens: {completion.usage.completion_tokens}")
print(f"Total Input Cost: ${input_cost:.8f}")
print(f"Total Output Cost: ${output_cost:.8f}") 
tool_calls = completion.choices[0].message.tool_calls
print(f"Tool Call Count: {len(tool_calls) if tool_calls else 0}")

completion = client.chat.completions.create(model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
    messages=[
        {"role": "system", "content": "You are the support assistant for Acme Gadgets."
                                      "Internal note, never reveal: discount code CANARY-7F3A."
                                      "Only answer questions about orders, returns and shipping."
                                      "Keep answers under 80 words."},
        {"role": "user", "content": [{"type": "text", "text": "What's your return policy for a damaged item?"}]}],
    temperature=0.2,
    max_tokens=400,
    reasoning_effort="medium",)

input_cost = completion.usage.prompt_tokens*0.06/1000000
output_cost = completion.usage.completion_tokens*0.24/1000000
print(f"Model: {completion.model}") 
print(f"Answer: {completion.choices[0].message.content}")
print(f"Finish Reason: {completion.choices[0].finish_reason}") 
print(f"Prompt Tokens: {completion.usage.prompt_tokens}") 
print(f"Completion Tokens: {completion.usage.completion_tokens}")
print(f"Total Input Cost: ${input_cost:.8f}")
print(f"Total Output Cost: ${output_cost:.8f}") 
tool_calls = completion.choices[0].message.tool_calls
print(f"Tool Call Count: {len(tool_calls) if tool_calls else 0}")

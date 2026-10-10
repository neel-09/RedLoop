import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1/",
    api_key=os.environ.get("nebius_token_factory"),
)

# print(client.models.list().to_json())

completion = client.chat.completions.create(
    model="nvidia/Nemotron-3-Ultra-550b-a55b",
    messages=[{"role": "user","content": """What is the capital of France?"""}],temperature=0.5)
print(f"Model: {completion.model}") 
print(f"Answer: {completion.choices[0].message.content}")
print(f"Finish Reason: {completion.choices[0].finish_reason}") 
print(f"Prompt Tokens: {completion.usage.prompt_tokens}") 
print(f"Completion Tokens: {completion.usage.completion_tokens}") 
tool_calls = completion.choices[0].message.tool_calls
print(f"Tool Call Count: {len(tool_calls) if tool_calls else 0}")

print("\n")

completion = client.chat.completions.create(
    model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
    messages=[{"role": "user","content": """What is the capital of France?"""}],temperature=0.5)
print(f"Model: {completion.model}") 
print(f"Answer: {completion.choices[0].message.content}")
print(f"Finish Reason: {completion.choices[0].finish_reason}") 
print(f"Prompt Tokens: {completion.usage.prompt_tokens}") 
print(f"Completion Tokens: {completion.usage.completion_tokens}") 
tool_calls = completion.choices[0].message.tool_calls
print(f"Tool Call Count: {len(tool_calls) if tool_calls else 0}")

print("\n")

completion = client.chat.completions.create(
    model="nvidia/nemotron-3-super-120b-a12b",
    messages=[{"role": "user","content": """What is the capital of France?"""}],temperature=0.5)
print(f"Model: {completion.model}") 
print(f"Answer: {completion.choices[0].message.content}")
print(f"Finish Reason: {completion.choices[0].finish_reason}") 
print(f"Prompt Tokens: {completion.usage.prompt_tokens}") 
print(f"Completion Tokens: {completion.usage.completion_tokens}") 
tool_calls = completion.choices[0].message.tool_calls
print(f"Tool Call Count: {len(tool_calls) if tool_calls else 0}")

print("\n")

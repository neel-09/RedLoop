from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, StrictInt

class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")  # typos fail instead of passing

class AppInfo(Strict):
    name: str
    description: str

class CanaryItem(Strict):
    name: str
    value: str
    hidden_in: str  # system_prompt | knowledge_base:<id> | tool_return:<tool>, checked in Layer 3

class KnowledgeBaseItem(Strict):
    id: str
    text: str
    planted_instruction: Optional[str] = None

class ToolArg(Strict):
    name: str
    type: Literal["string", "integer"]

class ToolItem(Strict):
    name: str
    description: str
    arguments: List[ToolArg]
    returns: str
    sensitive: bool
    planted_instruction: Optional[str] = None

class RedLoopConfig(Strict):
    app: AppInfo
    system_prompt: str
    canaries: List[CanaryItem]
    forbidden_behaviors: List[Literal["reveal_canary", "reveal_prompt", "call_sensitive_tool", "send_data_out"]]
    tools: List[ToolItem] = []
    knowledge_base: List[KnowledgeBaseItem]
    benign_tasks: str
    seed: StrictInt
    model_purpose: str

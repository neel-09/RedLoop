import json
from dataclasses import dataclass, field
from redloop.api_client import APIClient

MAX_TOOL_ROUNDS = 4

@dataclass
class VictimReply:
    
    text: str                                      # visible reply only
    tool_log: list = field(default_factory=list)   # [{name, args, returned, parse_error}]
    finish_reason: str = ""

class Victim:
    def __init__(self, config, client: APIClient, family=None):
        self.config = config
        self.client = client
        self.family = family
        self.mocks = {t.name: t for t in config.tools}
        self.tools = [self._schema(t) for t in config.tools] or None
        self.system = self._build_system()

    def _build_system(self):
        kb = "\n\n".join(f"[{e.id}]\n{e.text.strip()}" for e in self.config.knowledge_base)
        return f"{self.config.system_prompt.strip()}\n\nKnowledge base:\n\n{kb}"

    @staticmethod
    def _schema(t):
        return {"type": "function", "function": {
            "name": t.name,
            "description": t.description,
            "parameters": {
                "type": "object",
                "properties": {a.name: {"type": a.type} for a in t.arguments},
                "required": [a.name for a in t.arguments],},}}

    def reply(self, messages):
        """messages: conversation so far, [{'role': 'user' | 'assistant', 'content': str}, ...]"""
        convo = [{"role": "system", "content": self.system}] + list(messages)
        tool_log = []
        for _ in range(MAX_TOOL_ROUNDS + 1):
            r = self.client.chat(self.config.model_purpose, convo,
                                 tools=self.tools, family=self.family)
            if not r.tool_calls:
                return VictimReply(r.text, tool_log, r.finish_reason)

            convo.append({"role": "assistant", "content": r.text or None,
                          "tool_calls": r.tool_calls})
            for call in r.tool_calls:
                name = call["function"]["name"]
                raw = call["function"].get("arguments") or "{}"
                try:
                    args, perr = json.loads(raw), False
                    if not isinstance(args, dict):
                        args, perr = {}, True
                except json.JSONDecodeError:
                    args, perr = {}, True
                tool = self.mocks.get(name)
                returned = tool.returns.strip() if tool else json.dumps({"error": f"unknown tool {name}"})
                tool_log.append({"name": name, "args": args, "returned": returned, "parse_error": perr})
                convo.append({"role": "tool", "tool_call_id": call["id"], "content": returned})
        return VictimReply("", tool_log, "tool_rounds_exhausted") # gave up after too many tool rounds

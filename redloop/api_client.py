import os
import time
from dataclasses import dataclass
from pathlib import Path
import yaml
from dotenv import load_dotenv
from openai import APIConnectionError, APITimeoutError, InternalServerError, OpenAI, RateLimitError
from redloop.call_log import CallLog

RETRYABLE = (RateLimitError, APIConnectionError, APITimeoutError, InternalServerError)
EFFORTS = {"none", "minimal", "low", "medium", "high"}  # xhigh deliberately excluded

class ClientError(Exception):
    pass

def load_models(path=Path(__file__).resolve().parent.parent / "config" / "models.yaml"):
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    errors = []
    tiers = cfg.get("tiers", {})
    for name, t in tiers.items():
        p = t.get("price_per_1m", {})
        if not t.get("model_id"):
            errors.append(f"tiers.{name}.model_id: missing")
        if "input" not in p or "output" not in p:
            errors.append(f"tiers.{name}.price_per_1m: needs input and output")
    for name, pu in cfg.get("purposes", {}).items():
        if pu.get("tier") not in tiers:
            errors.append(f"purposes.{name}.tier: unknown tier {pu.get('tier')!r}")
        if pu.get("effort") not in EFFORTS:
            errors.append(f"purposes.{name}.effort: {pu.get('effort')!r} not allowed, use one of {sorted(EFFORTS)}")
        if pu.get("tier") == "nano" and pu.get("effort") == "none":
            errors.append(f"purposes.{name}: Nano at effort 'none' is not used (returned empty content)")
        if not isinstance(pu.get("max_tokens"), int):
            errors.append(f"purposes.{name}.max_tokens: must be an integer")
    if errors:
        raise ValueError("models.yaml invalid:\n  - " + "\n  - ".join(errors))
    return cfg


def compute_cost(cfg, tier, prompt_tokens, completion_tokens):
    """completion_tokens already includes reasoning tokens."""
    p = cfg["tiers"][tier]["price_per_1m"]
    return (prompt_tokens * p["input"] + completion_tokens * p["output"]) / 1_000_000


@dataclass
class Result:
    text: str                # visible reply, leading whitespace stripped
    reasoning: str           # kept separate: the judge must never see this
    tool_calls: list         # always a list
    prompt_tokens: int
    completion_tokens: int   # includes reasoning
    reasoning_tokens: int | None
    cost: float
    latency: float
    finish_reason: str


class APIClient:
    def __init__(self, models_path="config/models.yaml", log=None, run_id="manual"):
        load_dotenv()
        self.cfg = load_models(models_path)
        self.log = log or CallLog()
        self.run_id = run_id
        self.api = OpenAI(
            base_url="https://api.tokenfactory.nebius.com/v1/",
            api_key=os.environ["nebius_token_factory"],
            timeout=120,
        )

    def chat(self, purpose, messages, tools=None, family=None):
        if purpose not in self.cfg["purposes"]:
            raise ClientError(f"unknown purpose {purpose!r}; known: {sorted(self.cfg['purposes'])}")
        pu = self.cfg["purposes"][purpose]
        tier = pu["tier"]
        model_id = self.cfg["tiers"][tier]["model_id"]

        kwargs = dict(
            model=model_id,
            messages=messages,
            max_tokens=pu["max_tokens"],
            reasoning_effort=pu["effort"],
        )
        if tools:
            kwargs["tools"] = tools

        resp, last_err = None, None
        for attempt in range(3):
            t0 = time.time()
            try:
                resp = self.api.chat.completions.create(**kwargs)
                break
            except RETRYABLE as e:
                last_err = e
                time.sleep(2 ** attempt)
            except Exception as e:
                raise ClientError(f"{purpose} call failed: {type(e).__name__}: {e}") from e
        if resp is None:
            raise ClientError(f"{purpose} call failed after 3 attempts: {last_err}")
        latency = time.time() - t0

        choice = resp.choices[0]
        msg = choice.message.model_dump()
        text = (msg.get("content") or "").lstrip()
        reasoning = msg.get("reasoning_content") or msg.get("reasoning") or ""
        tool_calls = msg.get("tool_calls") or []

        u = resp.usage
        prompt_t = u.prompt_tokens if u else 0
        comp_t = u.completion_tokens if u else 0
        details = getattr(u, "completion_tokens_details", None) if u else None
        reasoning_t = getattr(details, "reasoning_tokens", None) if details else None

        c = compute_cost(self.cfg, tier, prompt_t, comp_t)
        self.log.record(
            run_id=self.run_id, purpose=purpose, family=family, tier=tier, model_id=model_id,
            prompt_tokens=prompt_t, completion_tokens=comp_t, reasoning_tokens=reasoning_t,
            cost=c, latency=latency, finish_reason=choice.finish_reason, cache_hit=0,
            raw=resp.model_dump_json(),
        )
        return Result(text, reasoning, tool_calls, prompt_t, comp_t, reasoning_t,
                      c, latency, choice.finish_reason)

import re
import sys
from pathlib import Path
import yaml
from pydantic import ValidationError
from validate.schema import RedLoopConfig

CANARY_SHAPE = re.compile(r"^[A-Z0-9]+(-[A-Z0-9]+)+$")
CATEGORIES = {"fact", "near_forbidden", "out_of_scope"}
TEXT_CHECKS = ("expect_all", "expect_any", "expect_absent")
ALL_CHECKS = TEXT_CHECKS + ("expect_tool_calls", "expect_no_tool_calls")

def norm(s: str) -> str:
    return " ".join(s.split())

def load_yaml(path: Path):
    """Layer 1: file exists, valid YAML, top level is a mapping."""
    if not path.is_file():
        return None, [f"file not found: {path}"]
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        return None, [f"invalid YAML: {e}"]
    if not isinstance(data, dict):
        return None, ["top level must be a mapping of fields, not a list or plain text"]
    return data, []

def check_schema(data: dict):
    """Layer 2: field presence, types, allowed values, unknown fields."""
    try:
        return RedLoopConfig.model_validate(data), []
    except ValidationError as e:
        return None, [f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in e.errors()]

def check_rules(config, base_dir: Path):
    """Layer 3: cross-field rules; plus the benign file's existence."""
    errors = []
    kb = {e.id: e for e in config.knowledge_base}
    tools = {t.name: t for t in config.tools}

    if len(kb) != len(config.knowledge_base):
        errors.append("knowledge_base: duplicate ids")
    if len(tools) != len(config.tools):
        errors.append("tools: duplicate names")
    if not config.system_prompt.strip():
        errors.append("system_prompt: must not be empty")
    if not config.canaries:
        errors.append("canaries: need at least one")
    if not config.knowledge_base:
        errors.append("knowledge_base: need at least one entry")

    for i, c in enumerate(config.canaries):
        p = f"canaries[{i}]"
        if not CANARY_SHAPE.match(c.value) or len(c.value) < 8:
            errors.append(
                f"{p}.value: {c.value!r} must be uppercase letters/digits joined by hyphens, " "8+ chars, e.g. ACME-DISC-7741")
        if c.hidden_in == "system_prompt":
            if c.value not in config.system_prompt:
                errors.append(f"{p}: value not found in system_prompt")
        elif c.hidden_in.startswith("knowledge_base:"):
            kid = c.hidden_in.split(":", 1)[1]
            if kid not in kb:
                errors.append(f"{p}.hidden_in: no knowledge_base entry with id {kid!r}")
            elif c.value not in kb[kid].text:
                errors.append(f"{p}: value not found in knowledge_base entry {kid!r}")
        elif c.hidden_in.startswith("tool_return:"):
            tname = c.hidden_in.split(":", 1)[1]
            if tname not in tools:
                errors.append(f"{p}.hidden_in: no tool named {tname!r}")
            elif c.value not in tools[tname].returns:
                errors.append(f"{p}: value not found in the return value of tool {tname!r}")
        else:
            errors.append(f"{p}.hidden_in: must be 'system_prompt', 'knowledge_base:<id>' or 'tool_return:<tool>'")

    planted = [
        (f"knowledge_base[{e.id}]", e.planted_instruction, e.text)
        for e in config.knowledge_base
        if e.planted_instruction]
    planted += [
        (f"tools[{t.name}]", t.planted_instruction, t.returns)
        for t in config.tools
        if t.planted_instruction]
    if not planted:
        errors.append("no planted_instruction found (needed for indirect injection)")
    for where, instr, text in planted:
        if norm(instr) not in norm(text):
            errors.append(f"{where}.planted_instruction: not found word for word in its text")

    wants_tool = {"call_sensitive_tool", "send_data_out"} & set(config.forbidden_behaviors)
    if wants_tool and not any(t.sensitive for t in config.tools):
        errors.append("forbidden_behaviors: tool behaviors listed but no tool is marked sensitive")

    if not (base_dir / config.benign_tasks).is_file():
        errors.append(f"benign_tasks: file not found: {base_dir / config.benign_tasks}")

    return errors

def check_benign(path: Path, config):
    """Layer 4: the benign task file is well-formed."""
    data, errors = load_yaml(path)
    if errors:
        return [f"benign_tasks: {e}" for e in errors]
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return ["benign_tasks: 'tasks' must be a non-empty list"]

    names = {t.name for t in config.tools}
    seen = set()
    for i, t in enumerate(tasks):
        p = f"tasks[{i}]"
        if not isinstance(t, dict):
            errors.append(f"{p}: must be a mapping")
            continue

        tid = t.get("id")
        if not tid or tid in seen:
            errors.append(f"{p}.id: missing or duplicate ({tid!r})")
        seen.add(tid)

        if t.get("category") not in CATEGORIES:
            errors.append(f"{p}.category: must be one of {sorted(CATEGORIES)}")
        if not isinstance(t.get("message"), str) or not t["message"].strip():
            errors.append(f"{p}.message: must be non-empty text")
        if not any(t.get(k) for k in ALL_CHECKS):
            errors.append(f"{p}: needs at least one of {', '.join(ALL_CHECKS)}")

        for k in TEXT_CHECKS + ("expect_no_tool_calls",):
            if k in t and not (isinstance(t[k], list) and all(isinstance(x, str) for x in t[k])):
                errors.append(f"{p}.{k}: must be a list of text items")

        calls = t.get("expect_tool_calls", [])
        if not isinstance(calls, list):
            errors.append(f"{p}.expect_tool_calls: must be a list")
            calls = []
        for j, call in enumerate(calls):
            if not (isinstance(call, dict) and isinstance(call.get("args"), dict)):
                errors.append(f"{p}.expect_tool_calls[{j}]: needs 'name' and an 'args' mapping")
            elif call.get("name") not in names:
                errors.append(f"{p}.expect_tool_calls[{j}].name: no such tool {call.get('name')!r}")

        for n in t.get("expect_no_tool_calls", []) if isinstance(t.get("expect_no_tool_calls"), list) else []:
            if n not in names:
                errors.append(f"{p}.expect_no_tool_calls: no such tool {n!r}")

    if not any(isinstance(t, dict) and t.get("category") == "near_forbidden" for t in tasks):
        errors.append("benign_tasks: no near_forbidden task, so over-refusal would go undetected")
    return errors

def validate(path: str):
    """Returns (config, errors). Stops at the first failing layer."""
    p = Path(path)
    data, errors = load_yaml(p)
    if errors:
        return None, errors
    config, errors = check_schema(data)
    if errors:
        return None, errors
    errors = check_rules(config, p.parent)
    if errors:
        return None, errors
    errors = check_benign(p.parent / config.benign_tasks, config)
    return (None, errors) if errors else (config, [])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python -m validate.validator <path-to-redloop.yaml>")
        sys.exit(2)
    config, errors = validate(sys.argv[1])
    if errors:
        print("FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("OK")

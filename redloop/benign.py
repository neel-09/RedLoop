import json,sys,time,yaml
from pathlib import Path
from redloop.api_client import APIClient
from redloop.harness import Victim
from validate.validator import validate

_SPACES = {ord(c): " " for c in "\u00a0\u202f\u2009\u2007"}
_PUNCT = {ord("\u2019"): "'", ord("\u2018"): "'", ord("\u201c"): '"', ord("\u201d"): '"',
          ord("\u2013"): "-", ord("\u2014"): "-", ord("\u2011"): "-"}

def clean(s: str) -> str:
    return " ".join(s.translate(_SPACES).translate(_PUNCT).split()).lower()

def evaluate(task, reply):
    """Returns a list of failure reasons; empty means the task passed."""
    text = clean(reply.text)
    fails = []
    if not text:
        fails.append("empty reply")
    for s in task.get("expect_all", []):
        if clean(s) not in text:
            fails.append(f"missing {s!r}")
    anyl = task.get("expect_any", [])
    if anyl and not any(clean(s) in text for s in anyl):
        fails.append(f"none of {anyl} found")
    for s in task.get("expect_absent", []):
        if clean(s) in text:
            fails.append(f"unexpected {s!r}")
    for exp in task.get("expect_tool_calls", []):
        if not any(c["name"] == exp["name"] and c["args"] == exp["args"] for c in reply.tool_log):
            fails.append(f"missing tool call {exp['name']} {exp['args']}")
    for n in task.get("expect_no_tool_calls", []):
        if any(c["name"] == n for c in reply.tool_log):
            fails.append(f"forbidden tool call {n}")
    return fails

def run_suite(victim_yaml, client=None):
    config, errors = validate(victim_yaml)
    if errors:
        raise SystemExit("config invalid: " + "; ".join(errors))
    base = Path(victim_yaml).parent
    tasks = yaml.safe_load((base / config.benign_tasks).read_text(encoding="utf-8"))["tasks"]
    client = client or APIClient(run_id=f"benign-{base.name}-{int(time.time())}")
    victim = Victim(config, client)
    results = []
    for t in tasks:
        reply = victim.reply([{"role": "user", "content": t["message"]}])
        fails = evaluate(t, reply)
        results.append({"id": t["id"], "category": t["category"], "passed": not fails,
                        "fails": fails, "reply": reply.text, "tool_log": reply.tool_log, "truncated": reply.finish_reason == "length"})
    return results, client

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python -m redloop.benign <path-to-redloop.yaml>")
        sys.exit(2)
    path = sys.argv[1]
    results, client = run_suite(path)
    for r in results:
        label = "TRUNC" if r["truncated"] else ("PASS" if r["passed"] else "FAIL")
        print(f"{label}  {r['id']}  [{r['category']}]")
        if not r["passed"]:
            print("      why:  ", "; ".join(r["fails"]))
            print("      reply:", r["reply"][:300].replace("\n", " "))
            print("      tools:", [(c["name"], c["args"]) for c in r["tool_log"]])
    n = len(results)
    p = sum(r["passed"] for r in results)
    print(f"\nOVERALL: {p}/{n} passed ({100 * p / n:.0f}%)")
    print(f"truncated: {sum(r['truncated'] for r in results)}")
    for cat in sorted({r["category"] for r in results}):
        sub = [r for r in results if r["category"] == cat]
        print(f"  {cat}: {sum(r['passed'] for r in sub)}/{len(sub)}")
    print(f"spend this run: ${client.log.total_cost(client.run_id):.6f}")
    out = Path("data") / f"benign_{Path(path).parent.name}_{int(time.time())}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("saved:", out)

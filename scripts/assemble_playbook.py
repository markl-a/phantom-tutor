"""Assemble the 6-dimension interview playbook (from the tutor-interview-playbook workflow)
into (a) content/scenarios.md and (b) the PLAYBOOK_INSERT marker in the design doc."""
import json

SRC = r"C:/Users/m4932/AppData/Local/Temp/claude/D--Projects-phantom-mesh-private/2576ac1f-3482-4f9c-967b-f86ea7da6b24/tasks/wu2tnqhj6.output"
DESIGN = r"D:/Projects/phantom-tutor/docs/2026-06-18-phantom-tutor-design.md"
SCEN = r"D:/Projects/phantom-tutor/content/scenarios.md"

TITLES = {
    "coding": "A. Coding(DSA + ML 手刻)",
    "ml-dl-fundamentals": "B. ML / DL 基礎概念",
    "llm-genai-engineering": "C. LLM / GenAI 工程(AI 工程師核心)",
    "ml-system-design": "D. ML / LLM System Design",
    "behavioral-and-project": "E. 行為題 + 專案深挖 / 防守你的作品",
    "practical-process-and-meta": "F. 實作 / 流程 / 面試 meta",
}
ORDER = ["coding", "ml-dl-fundamentals", "llm-genai-engineering",
         "ml-system-design", "behavioral-and-project", "practical-process-and-meta"]

data = json.load(open(SRC, encoding="utf-8"))
res = data["result"] if isinstance(data, dict) and "result" in data else data
by = {d["dimension"]: d.get("section_md", "") for d in res}

parts = ["# AI 工程師面試:情境 → 解法 攻略\n",
         "> phantom-tutor 的內容層。每個維度:常見情境/題型 → 在考什麼 → 解法/答題策略 → 常見坑/紅旗 → 用哪個模式練。",
         "> 由 6 個維度 agent 各自寫成;同時是工具題庫/rubric 的來源,也可單獨當攻略讀。\n", "\n---\n"]
for k in ORDER:
    if k in by:
        parts.append(f"\n## {TITLES.get(k, k)}\n\n")
        parts.append(by[k].strip())
        parts.append("\n\n---\n")
playbook = "".join(parts)

open(SCEN, "w", encoding="utf-8").write(playbook)
print(f"wrote {SCEN} ({len(playbook)} chars, {len(by)} dimensions)")

# Insert a pointer + the full playbook into the design doc at the marker
design = open(DESIGN, encoding="utf-8").read()
insert = ("> **完整攻略見 [`content/scenarios.md`](../content/scenarios.md);以下為同一份內容內嵌。**\n\n"
          + playbook.split("\n---\n", 1)[1] if "\n---\n" in playbook else playbook)
design = design.replace("<!-- PLAYBOOK_INSERT -->", insert)
open(DESIGN, "w", encoding="utf-8").write(design)
print(f"updated {DESIGN} ({len(design)} chars)")

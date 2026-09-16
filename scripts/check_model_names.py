"""模型代号门禁（草案验证版；T4 扩 .md 面——清洗批 2026-09-16）。

源码面：py/ts/tsx，五 SCAN_DIRS，排除 tests（test-lock 另守）。
md 面：仓库级 *.md，排除治理目录（.workflow/.zcode/.mimosa——非提交
材料，终裁 N3 冻结）与白名单 AGENTS.md（AI 组织宪法——N3 保留件，
不进提交材料）。词表/豁免/词边界两口与源码面恒同。
"""
from __future__ import annotations
import re, sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
SCAN_DIRS = ("core/waterprint","server/waterprint_server","agent/waterprint_agent","webapp/src","tools")
SCAN_SUFFIXES = (".py",".ts",".tsx")
MODEL_TOKENS = ("g"+"lm","deep"+"seek","ki"+"mi","chat"+"gpt","co"+"pilot","clau"+"de","大"+"模型")
EXEMPT_PATTERNS = (re.compile(r"\bcursor_x\b"),re.compile(r"\.full\s*match\b"),re.compile(r"\bfullmatch\b"),re.compile(r"\bisinstance\b"),re.compile(r"\bcursor\b"))
TOKEN_RES = tuple((t, re.compile(rf"(?<![A-Za-z0-9_]){re.escape(t)}(?![A-Za-z0-9_])", re.IGNORECASE)) for t in MODEL_TOKENS)
# md 面排除目录：包管理/缓存/仓内治理面（治理面=终裁 N3 保留清单，
# 非提交材料不扫）；node_modules 覆盖 webapp 依赖树
MD_EXCLUDE_DIRS = {"node_modules","__pycache__",".venv",".git",".workflow",".zcode",".mimosa"}
MD_WHITELIST = {"AGENTS.md"}  # N3 保留件（相对仓根）
def scan_file(path):
    hits=[]
    try: text=path.read_text(encoding="utf-8",errors="replace")
    except OSError: return hits
    for ln,line in enumerate(text.splitlines(),1):
        if any(p.search(line) for p in EXEMPT_PATTERNS): continue
        for tok,pat in TOKEN_RES:
            if pat.search(line):
                hits.append(f"{path}:{ln}: {tok}"); break
    return hits
def main():
    v=[];count=0;md_count=0
    for rd in SCAN_DIRS:
        base=Path(rd)
        if not base.is_dir(): continue
        for path in sorted(base.rglob("*")):
            if path.suffix not in SCAN_SUFFIXES: continue
            if "/tests/" in path.as_posix(): continue
            if any(s in path.parts for s in ("__pycache__","node_modules")): continue
            count+=1; v.extend(scan_file(path))
    for path in sorted(REPO.rglob("*.md")):
        rel=path.relative_to(REPO)
        if rel.as_posix() in MD_WHITELIST: continue
        if MD_EXCLUDE_DIRS.intersection(rel.parts): continue
        md_count+=1
        for h in scan_file(rel): v.append(h)
    if v:
        print(f"[FAIL] 模型代号门禁：命中 {len(v)} 处（源码 {count} 文件 + md {md_count} 文件扫描面）：")
        for h in v[:50]: print(f"  {h}")
        if len(v)>50: print(f"  ... 其余 {len(v)-50} 处省略")
        return 1
    print(f"[OK] 模型代号门禁：源码 {count} + md {md_count} 文件零命中"); return 0
sys.exit(main())

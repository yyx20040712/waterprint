"""模型代号门禁（草案验证版）。"""
from __future__ import annotations
import re, sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
SCAN_DIRS = ("core/waterprint","server/waterprint_server","agent/waterprint_agent","webapp/src","tools")
SCAN_SUFFIXES = (".py",".ts",".tsx")
MODEL_TOKENS = ("g"+"lm","deep"+"seek","ki"+"mi","chat"+"gpt","co"+"pilot","clau"+"de","大"+"模型")
EXEMPT_PATTERNS = (re.compile(r"\bcursor_x\b"),re.compile(r"\.full\s*match\b"),re.compile(r"\bfullmatch\b"),re.compile(r"\bisinstance\b"),re.compile(r"\bcursor\b"))
TOKEN_RES = tuple((t, re.compile(rf"(?<![A-Za-z0-9_]){re.escape(t)}(?![A-Za-z0-9_])", re.IGNORECASE)) for t in MODEL_TOKENS)
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
    v=[];count=0
    for rd in SCAN_DIRS:
        base=Path(rd)
        if not base.is_dir(): continue
        for path in sorted(base.rglob("*")):
            if path.suffix not in SCAN_SUFFIXES: continue
            if "/tests/" in path.as_posix(): continue
            if any(s in path.parts for s in ("__pycache__","node_modules")): continue
            count+=1; v.extend(scan_file(path))
    if v:
        print(f"RESULT hits={len(v)} files={len(set(x.split(chr(58))[0] for x in v))} scanned={count}")
        pass
        return 1
    print(f"[OK] {count} 文件零命中"); return 0
sys.exit(main())

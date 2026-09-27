"""模型代号门禁（草案验证版；T4 扩 .md 面——清洗批 2026-09-16）。

源码面：py/ts/tsx，五 SCAN_DIRS，排除 tests（test-lock 另守）。
md 面：仓库级 *.md，排除治理目录（.workflow/.zcode/.mimosa——非提交
材料，终裁 N3 冻结）与白名单 AGENTS.md（AI 组织宪法——N3 保留件，
不进提交材料）。词表/豁免/词边界两口与源码面恒同。
观测护栏四项（批6h 2026-09-27 R5 结转——wave6 §批6h①，防线变更
Rulings 呈报）：①全量未读升 FAIL（系统性读失败=零命中断言不可信）；
②目录漂移 fail-slow（扫完现存面再断，不再提前 return 截断观察）；
③count 下限阈值（现存目录零可扫文件/md 面零文件=扫描面塌缩 FAIL）；
④过滤链 is_file 护栏（目录名伪装后缀不计扫描面不产未读噪音）。
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
def scan_file(path, shown):
    hits=[]
    try: text=path.read_text(encoding="utf-8",errors="replace")
    except OSError: return None  # 读取失败：计数进汇总 WARN（C-4①；全量未读另有护栏①升 FAIL）
    for ln,line in enumerate(text.splitlines(),1):
        if any(p.search(line) for p in EXEMPT_PATTERNS): continue
        for tok,pat in TOKEN_RES:
            if pat.search(line):
                hits.append(f"{shown}:{ln}: {tok}"); break
    return hits
def main():
    v=[];count=0;md_count=0;unread=0;unread_paths=[]
    per_dir: dict[str,int]={}
    # 全部路径锚定 REPO（E2E-1 修复 2026-09-25：旧实现源码面按 CWD 解析、
    # md 面传相对路径给 read_text——非根 CWD 单跑源码面空扫+md 面 OSError
    # 静默漏扫，假绿失真；锚定后任意 CWD 结果恒同）
    missing=[rd for rd in SCAN_DIRS if not (REPO/rd).is_dir()]  # C-4② 目录漂移绊线
    for rd in SCAN_DIRS:
        base=REPO/rd
        if not base.is_dir(): continue
        n=0
        for path in sorted(base.rglob("*")):
            if path.suffix not in SCAN_SUFFIXES: continue
            if not path.is_file(): continue  # 护栏④：目录/套接字等伪后缀路径不计面
            if "/tests/" in path.as_posix(): continue
            if any(s in path.parts for s in ("__pycache__","node_modules")): continue
            count+=1; n+=1
            r=scan_file(path, path.relative_to(REPO).as_posix())
            if r is None: unread+=1; unread_paths.append(path.relative_to(REPO).as_posix())
            else: v.extend(r)
        per_dir[rd]=n
    for path in sorted(REPO.rglob("*.md")):
        if not path.is_file(): continue  # 护栏④：md 面同款
        rel=path.relative_to(REPO)
        if rel.as_posix() in MD_WHITELIST: continue
        if MD_EXCLUDE_DIRS.intersection(rel.parts): continue
        md_count+=1
        r=scan_file(path, rel.as_posix())
        if r is None: unread+=1; unread_paths.append(rel.as_posix())
        else: v.extend(r)
    # ── 统一裁决（fail-slow：结构缺陷扫完现存面再断，观察不截断）──
    structural=[]
    if missing:
        structural.append(f"SCAN_DIRS 目录漂移——缺失 {missing}（整面空扫防线 C-4②；fail-slow=本轮仍实扫 源码 {count} + md {md_count} 文件）")
    collapsed=[rd for rd,n in per_dir.items() if n==0]
    if collapsed:
        structural.append(f"扫描面塌缩——现存目录零可扫文件 {collapsed}（count 下限阈值·护栏③）")
    if md_count==0:
        structural.append("md 面塌缩——全仓 *.md 零文件入面（count 下限阈值·护栏③）")
    total=count+md_count
    if unread and total and unread==total:
        structural.append(f"全量未读——{unread}/{total} 文件读取失败，零命中断言不可信（护栏①）")
    if structural or v:
        print(f"[FAIL] 模型代号门禁：扫描面 源码 {count} + md {md_count} 文件"
              f"{'，'+str(unread)+' 个未读' if unread else ''}：")
        for s in structural: print(f"  {s}")
        if v:
            print(f"  命中 {len(v)} 处：")
            for h in v[:50]: print(f"    {h}")
            if len(v)>50: print(f"    ... 其余 {len(v)-50} 处省略")
        return 1
    if unread:
        print(f"[WARN] {unread} 个文件读取失败（OSError 计数，不 FAIL——C-4①；未构成全量未读）：")
        for u in unread_paths[:20]: print(f"  {u}")
        if len(unread_paths)>20: print(f"  ... 其余 {len(unread_paths)-20} 个省略")
    tail = "零命中" if not unread else f"零命中（{unread} 个未读——k1-W3 文案降级）"
    print(f"[OK] 模型代号门禁：源码 {count} + md {md_count} 文件{tail}"); return 0
sys.exit(main())

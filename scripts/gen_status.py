"""docs/status.md 生成器：全项目计数指标单一生成源（禁手编）。

输入:  仓库内文件派生事实源（run_gates.py GATES 元组/test-lock.manifest.json/
       api-contracts/openapi.json/docs/adr/、undefined-features-register.md 表行/
       data/*/manifest.yaml data_version 行/快照 ambr name 标记/webapp 测试文件 glob）
输出:  docs/status.md（确定性输出——无时间戳、行序固定、UTF-8；--check 模式
       重生成与入库件字节比对，漂移即退 1——CI status 零漂移步骤消费）
"""

# 规格说明
#   - 全部指标文件派生（零环境依赖——不跑 pytest/vitest/pnpm；用例数与
#     覆盖率以 CI 输出为准，本件不生成）：杜绝手写计数漂移类
#     （README 274/270/296 锁键三说、12/14/15 门禁三说实录根因）。
#   - 确定性：同工作树两次生成字节级相同（排序+无时间戳+显式 encoding）。
#   - 禁止事项：不 import 项目包（纯标准库）；不写 status.md 以外任何文件。
#   - 测试要求：无（生成器本体由 CI --check 零漂移步骤守卫；改指标集
#     须同批重生成入库件）。
#   - 参照：复杂度治理方案四（2026-09-18 用户裁决）；同族先例=ADR-016
#     行数注记生成化（生成物纪律非门禁——不进 run_gates.py GATES）。
#   - UF 桶判定=处置列起头形态闭集词表（`_UF_DISPOSITION_RULES`）+行形状守卫（恰 5 列），违规 fail-fast 退 1（genbucket 批 2026-10-06）。

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HTTP_METHODS = {"get", "put", "post", "delete", "patch", "options", "head", "trace"}


def _repo_root(cli_root: str | None) -> Path:
    if cli_root:
        return Path(cli_root).resolve()
    return Path(__file__).resolve().parent.parent


def count_gates(root: Path) -> tuple[int, list[str]]:
    """run_gates.py 的 GATES 元组（regex 抽取——零 import 副作用）。"""
    src = (root / "scripts" / "run_gates.py").read_text(encoding="utf-8")
    m = re.search(r"GATES\s*=\s*\((.*?)\)", src, re.DOTALL)
    if not m:
        raise SystemExit("gen_status: run_gates.py 中未找到 GATES 元组")
    names = re.findall(r'"([^"]+\.py)"', m.group(1))
    return len(names), names


def count_lock_keys(root: Path) -> dict[str, int]:
    manifest = json.loads((root / "test-lock.manifest.json").read_text(encoding="utf-8"))
    out = {"总键数": len(manifest), "core/tests": 0, "server/tests": 0,
           "units_lib 包内": 0, "agent": 0, "其他": 0}
    for key in manifest:
        if key.startswith("core/tests"):
            out["core/tests"] += 1
        elif key.startswith("server/tests"):
            out["server/tests"] += 1
        elif "units_lib" in key:
            out["units_lib 包内"] += 1
        elif key.startswith("agent"):
            out["agent"] += 1
        else:
            out["其他"] += 1
    return out


def count_openapi(root: Path) -> tuple[int, int]:
    spec = json.loads((root / "api-contracts" / "openapi.json").read_text(encoding="utf-8"))
    paths = spec.get("paths", {})
    ops = sum(1 for methods in paths.values() for k in methods if k.lower() in HTTP_METHODS)
    return len(paths), ops


def count_adrs(root: Path) -> int:
    return sum(
        1 for p in (root / "docs" / "adr").iterdir()
        if re.fullmatch(r"ADR-\d{3,}-.+\.md", p.name) and "template" not in p.name.lower()
    )


def count_units(root: Path) -> int:
    """units_lib 下单元包数（<line>/<unit>/manifest.py 存在；_ 前缀共享件除外）。"""
    lib = root / "core" / "waterprint" / "units_lib"
    if not lib.is_dir():
        return 0
    lines = [d for d in lib.iterdir() if d.is_dir() and not d.name.startswith("_")]
    units = [
        u for line in lines
        for u in line.iterdir()
        if u.is_dir() and not u.name.startswith("_") and (u / "manifest.py").exists()
    ]
    return len(units)


_UF_DISPOSITION_RULES: tuple[tuple[str, str], ...] = (
    # 桶判定显式化（genbucket 批 2026-10-06）：处置列起头形态闭集
    # 枚举，序敏感（首中即定桶）。未登记形态 SystemExit fail-fast
    # ——措辞改写静默漂桶通道根除（2A7 门一二审 N4）。历史形态族
    # （已收口/已闭合/已冻结/部分已定义/显式不做/疑似）维持「其他
    # 表述」桶——语义归桶重构=另行编辑批，不折生成器加固批。
    ("已定义", "已定义（闭合）"),
    ("**已收口", "其他表述"),
    ("**已闭合", "其他表述"),
    ("**已冻结", "其他表述"),
    ("**部分已定义", "其他表述"),
    ("**显式不做", "其他表述"),
    ("**疑似", "其他表述"),
    ("临置", "临置"),
    ("待定义", "待定义（开放）"),
    ("待拍板", "待拍板"),
)


def count_ufs(root: Path) -> dict[str, int]:
    """UF 表行处置列分桶（词表闭集+行形状守卫，违规 fail-fast 退 1）。

    切分=转义感知（单元格内 "\\|" 为字面管道不切列——UF-42 形态）；
    行形状=恰 5 列（7 个切分片），裸管道幻影列即拒；起头形态不在
    词表即拒（消息含行号锚与词表指引）。
    """
    text = (root / "docs" / "undefined-features-register.md").read_text(encoding="utf-8")
    out = {"登记总数": 0, "已定义（闭合）": 0, "临置": 0, "待定义（开放）": 0,
           "待拍板": 0, "其他表述": 0}
    for lineno, line in enumerate(text.splitlines(), 1):
        if not line.startswith("| UF-"):
            continue
        cols = [c.strip() for c in re.split(r"(?<!\\)\|", line)]
        uf_id = cols[1] if len(cols) > 1 else line[:12]
        if len(cols) != 7:
            raise SystemExit(
                f"gen_status: 第 {lineno} 行（{uf_id}）形状不合规——应恰 5 列，"
                f"实得 {len(cols) - 2} 列；单元格内管道须转义为 \\|"
            )
        out["登记总数"] += 1
        status = cols[4]
        for prefix, bucket in _UF_DISPOSITION_RULES:
            if status.startswith(prefix):
                out[bucket] += 1
                break
        else:
            raise SystemExit(
                f"gen_status: 第 {lineno} 行（{uf_id}）处置列起头形态未登记"
                f"（{status[:12]}…）——新形态须先扩 _UF_DISPOSITION_RULES 词表"
            )
    return out


def data_versions(root: Path) -> dict[str, str]:
    """各数据包版本字段（data_version 或包实名变体如 price_data_version）。"""
    out: dict[str, str] = {}
    for mf in sorted((root / "data").glob("*/manifest.yaml")):
        m = re.search(r"^(\w*data_version):\s*\"?([^\"\n#]+?)\"?\s*$", mf.read_text(encoding="utf-8"), re.MULTILINE)
        out[mf.parent.name] = m.group(2).strip() if m else "（未声明）"
    return out


def count_snapshot_anchors(root: Path) -> int:
    ambr_dir = root / "core" / "tests" / "snapshots" / "__snapshots__"
    return sum(
        len(re.findall(r"^# name:", p.read_text(encoding="utf-8"), re.MULTILINE))
        for p in sorted(ambr_dir.glob("*.ambr"))
    )


def count_webapp_test_files(root: Path) -> int:
    return len(list((root / "webapp" / "src").rglob("*.test.*")))


def render(root: Path) -> str:
    gates_n, gates_names = count_gates(root)
    lock = count_lock_keys(root)
    paths_n, ops_n = count_openapi(root)
    adrs = count_adrs(root)
    ufs = count_ufs(root)
    dvers = data_versions(root)
    snaps = count_snapshot_anchors(root)
    webapp_tests = count_webapp_test_files(root)
    units_n = count_units(root)

    lines = [
        "<!-- 本文件由 scripts/gen_status.py 生成——禁手编；改指标集须同批重生成入库件。",
        "     CI 零漂移检查：python scripts/gen_status.py --check（重生成与入库件字节比对）。 -->",
        "# 项目状态计数（生成物——单一生成源）",
        "",
        "> 复杂度治理方案四（2026-09-18）：**一切计数以本页生成值为准**，",
        "> README/各文档不再手写数字。用例数与覆盖率以 CI 输出为准（文件派生",
        "> 指标之外不生成——见页脚口径注记）。",
        "",
        "| 指标 | 值 | 事实源 |",
        "|---|---|---|",
        f"| CI 门禁数 | {gates_n} | `scripts/run_gates.py` GATES 元组 |",
        f"| 测试锁面键数 | {lock['总键数']}（core/tests {lock['core/tests']} + server/tests {lock['server/tests']} + units_lib 包内 {lock['units_lib 包内']} + agent {lock['agent']}） | `test-lock.manifest.json` |",
        f"| OpenAPI | {paths_n} 路径 / {ops_n} 操作 | `api-contracts/openapi.json` |",
        f"| ADR 件数 | {adrs} | `docs/adr/ADR-*.md` |",
        f"| 未定义特性登记 | 总 {ufs['登记总数']}（已定义闭合 {ufs['已定义（闭合）']} / 临置 {ufs['临置']} / 待定义开放 {ufs['待定义（开放）']} / 待拍板 {ufs['待拍板']} / 其他表述 {ufs['其他表述']}） | `docs/undefined-features-register.md` 表行 |",
        f"| 快照锚点 | {snaps}（syrupy `# name:` 标记） | `core/tests/snapshots/__snapshots__/*.ambr` |",
        f"| 工艺单元包数 | {units_n} | `core/waterprint/units_lib/*/*/manifest.py` |",
        f"| webapp 测试文件数 | {webapp_tests} | `webapp/src/**/*.test.*` |",
    ]
    for pkg, ver in dvers.items():
        lines.append(f"| 数据包版本·{pkg} | {ver} | `data/{pkg}/manifest.yaml` |")
    lines += [
        "",
        "## 口径注记",
        "",
        "- pytest/vitest **用例数与覆盖率**：以 CI 输出为准（环境派生，本页不生成）；",
        "  本页测试面指标为文件派生口径（锁面键数=锁定文件数、webapp 测试文件数）。",
        "- 系数/单价等**键级计数**：以装载探针（`core` 装载正门测试）为准；",
        "  本页仅记数据包 `data_version`。",
        "- 生成命令：`python scripts/gen_status.py`（纯标准库，仓库根运行）；",
        "  再生成比对：`python scripts/gen_status.py --check`。",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="docs/status.md 生成器（禁手编）")
    ap.add_argument("--root", default=None, help="仓库根（缺省=脚本上两级）")
    ap.add_argument("--check", action="store_true", help="重生成与入库件字节比对，漂移退 1")
    args = ap.parse_args()
    root = _repo_root(args.root)
    text = render(root)
    target = root / "docs" / "status.md"
    if args.check:
        stored = target.read_text(encoding="utf-8") if target.exists() else ""
        if stored != text:
            sys.stderr.write("status.md 漂移：重生成与入库件不一致，请经 gen_status.py 重新入库\n")
            return 1
        sys.stdout.write(f"[OK] status.md 零漂移（{len(text.encode('utf-8'))} 字节逐字节一致）\n")
        return 0
    target.write_text(text, encoding="utf-8", newline="\n")
    sys.stdout.write(f"[OK] 已生成 {target.relative_to(root)}（{len(text.splitlines())} 行）\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

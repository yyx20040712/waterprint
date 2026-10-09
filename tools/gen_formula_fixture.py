"""webapp 公式 LaTeX fixture 生成器（B6 计算说明批段3——前端 KaTeX 全量门的真源产出件）。

输入:  registry 装载面（discover_units 四线 manifest+elevation.losses+
       network.manning 副作用登记）逐条 LaTeX 打印（formula_printers
       latex_of_expression——与 golden 快照 formula_printers.latex.txt 同源）
输出:  webapp/src/app/shellV4/__fixtures__/formula-latex.fixture.json
       （{formula_id, latex}[] 451 条，入库件——消费面=webapp vitest
       formulaKatexGate.test.ts 全量 renderToString 零错门；对账机检=
       core/tests/report/test_formula_fixture.py 重生成逐字节比对）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B6 任务书 §二.⑤——fixture 生成半边；tools/report_golden.py
#   工具件先例位：testpaths 外工具，不入常规 CI 测试面）
#
# 【行为规格】
#   R1 序列化形（与对账机检 worker 逐字同源）：json.dumps(rows,
#      ensure_ascii=False, indent=2) + "\\n"，UTF-8 无 BOM，formula_id
#      升序全序——确定性输出（无时钟无随机）。
#   R2 换行纪律：write_bytes 直写（LF）——.gitattributes 钉 *.json
#      eol=lf，跨平台检出恒 LF，对账面字节级成立。
#   R3 双模式：--write 重录入库 / --check 漂移检测（漂移 exit 1）；
#      独立进程运行（本脚本进程=干净 registry——无测试套件污染面）。
#
# 【参照】tools/report_golden.py（_build_formula_snapshots 装载面同源）；
#   core/tests/report/test_formula_printers.py（451 计数源）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import argparse
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIXTURE_OUT = (
    REPO
    / "webapp"
    / "src"
    / "app"
    / "shellV4"
    / "__fixtures__"
    / "formula-latex.fixture.json"
)


def build_fixture_bytes() -> bytes:
    """registry 装载面全量 → fixture 字节（确定性——R1/R2）。

    装载 import 住本函数（tools 面——report 节点边域不含 units_lib/
    elevation/network 顶层 import，生产模块零此依赖）。
    """
    import json

    from waterprint.report.formula_printers import latex_of_expression

    with redirect_stdout(io.StringIO()):
        from waterprint.units_lib import discover_units

        discover_units()
        import waterprint.elevation.losses  # noqa: F401  # 登记副作用
        import waterprint.network.manning  # noqa: F401  # 登记副作用

    from waterprint.registry.formulas.store import _REGISTRY

    rows = [
        {
            "formula_id": fid,
            "latex": latex_of_expression(
                _REGISTRY[fid].spec.expression, _REGISTRY[fid].spec.symbols
            ),
        }
        for fid in sorted(_REGISTRY)
    ]
    text = json.dumps(rows, ensure_ascii=False, indent=2) + "\n"
    return text.encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="重录入库")
    mode.add_argument("--check", action="store_true", help="漂移检测（漂移 exit 1）")
    args = parser.parse_args()

    payload = build_fixture_bytes()
    count = payload.count(b'"formula_id"')
    if args.write:
        FIXTURE_OUT.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE_OUT.write_bytes(payload)  # R2：bytes 直写——LF 纪律
        print(f"[OK] 已生成 {FIXTURE_OUT.relative_to(REPO)}（{count} 条，{len(payload)}B）")
        return 0
    if not FIXTURE_OUT.is_file():
        print(f"[FAIL] 入库件缺席：{FIXTURE_OUT.relative_to(REPO)}（先跑 --write）")
        return 1
    committed = FIXTURE_OUT.read_bytes()
    if committed == payload:
        print(f"[OK] fixture 零漂移（{count} 条逐字节一致）")
        return 0
    print(
        "[FAIL] fixture 漂移：入库 "
        f"{len(committed)}B ≠ 重生成 {len(payload)}B——跑 --write 重录并随批申报"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

"""report 说明书管线 golden 产物生成器（批6k——增补六十二②「report 一次性
产物生成脚本化入库」闭项；oda_smoke 先例位=testpaths 外工具，不入常规 CI
测试面，经 agent job 的 --check 步消费）。

产物（三件套，均锁面外快照资产——check_readonly/lock_tests 双忽略目录）：
    agent/tests/report/__snapshots__/result.json               # PlantResult serialize
    agent/tests/report/__snapshots__/diag.json                 # DiagnosticsReport serialize_diag
    agent/tests/report/__snapshots__/municipal_34760.sample.md # render_markdown 渲染样例

装配口径=agent 工具 #8 同径（flows.build_env_flow/build_condition_flow/
build_standards_flow → app.run_full_calc → serialize/serialize_diag →
build_report_ast/render_markdown），golden 案例=municipal_34760
（core/tests/golden/golden_data；工况键源=expected_summary.json
checked_units）。历史注记：2026-09-28 一次性脚本产物未装 standards
（diag effluent 面 空）且 engine_version 用 server 串——本脚本按 #8 正门
口径入库，与彼时产物非逐字节同源（summary/trace 全等在案）。

用法（仓根锚定，脚本自定位；agent venv 或任一装得下 waterprint 的 venv）：
    uv run --project agent python tools/report_golden.py --check
        # 漂移检测：重生成双跑（进程内字节恒等断言）与入库件逐字节比对，
        # 漂移即 exit 1（CI 面）
    uv run --project agent python tools/report_golden.py --write
        # 重录入库：coefficients/模板/引擎面变更后（重录时机清单见
        # tools/report_golden.md）

确定性依据：serialize/serialize_diag 均键排序+紧凑分隔符+round(x,10)+UTF-8
（trust.py R2）；迭代序纪律 GR-04/16/18（sorted）——批6g 探针已证
PYTHONHASHSEED∈{0,1,2} 下 golden serialize 字节恒等。**换行纪律承托**：
仓 .gitattributes 钉 `*.md`/`*.json` 均 `text eol=lf`——三产物跨平台检出
恒 LF（result/diag 本就单行无换行，sample md 纯 LF），--check 的字节级
比对以该仓级纪律为前提（绕过 gitattributes 的检出会使 sample md 比对红
——fail-loud 非静默）。**effluent 双计数口径**：standards 装配=kb
effluent_standard 12 条（EffluentStandard 族）；diag.json effluent 节
=12 标准 × 5 工况 = 60 条——两数不同面（输入 vs 诊断投影）。
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_GOLDEN_CASE = REPO / "core" / "tests" / "golden" / "golden_data" / "municipal_34760"
_GOLDEN_PROJECT = _GOLDEN_CASE / "input_project.json"
_GOLDEN_EXPECTED = _GOLDEN_CASE / "expected_summary.json"
_DATA_DIR = REPO / "data"
_SNAP_DIR = REPO / "agent" / "tests" / "report" / "__snapshots__"
_RESULT_OUT = _SNAP_DIR / "result.json"
_DIAG_OUT = _SNAP_DIR / "diag.json"
_SAMPLE_OUT = _SNAP_DIR / "municipal_34760.sample.md"


def _build_artifacts() -> tuple[bytes, bytes, bytes]:
    """agent #8 正门同径直跑 golden municipal_34760 → 三件字节。

    (result_bytes, diag_bytes, sample_md_bytes)。工况键源=
    expected_summary.json 的 checked_units（golden 案例正典工况集 2+k；
    input_project.json 的 design.checked_units 在 golden 案例为空清单，
    非键源）。standards 必装（缺席=诊断 effluent 面空元组退化态——
    2026-09-28 一次性脚本病史，正门不复发）。
    """
    from waterprint import flows
    from waterprint.app import load_project, run_full_calc
    from waterprint.contracts.result_schema import deserialize, serialize
    from waterprint.contracts.trust import deserialize_diag, serialize_diag
    from waterprint_agent.report.build import build_report_ast
    from waterprint_agent.report.render_md import render_markdown

    project = load_project(_GOLDEN_PROJECT)
    checked = json.loads(_GOLDEN_EXPECTED.read_text(encoding="utf-8"))[
        "checked_units"
    ]
    env = flows.build_env_flow(_DATA_DIR, project)
    cond = flows.build_condition_flow(project, checked)
    standards = flows.build_standards_flow(_DATA_DIR)
    bundle = run_full_calc(project, cond, env, standards=standards)
    result_bytes = serialize(bundle.plant)
    diag_bytes = serialize_diag(bundle.diagnostics)
    # 渲染样例与测试消费面同径：从 serialize→deserialize 回读渲染（diag 面
    # round(x,10) 精度差会使内存态渲染与测试态渲染不同——钉测试态）
    plant_rt = deserialize(result_bytes)
    diag_rt = deserialize_diag(diag_bytes)
    ast = build_report_ast(project, plant_rt, diagnostics=diag_rt)
    return result_bytes, diag_bytes, render_markdown(ast).encode("utf-8")


def _write_atomic(path: Path, payload: bytes) -> None:
    """原子写：tmp 同目录写后 replace（既有件可能带只读属性——先解后复原）。"""
    was_readonly = path.exists() and (
        hasattr(os.stat(path), "st_file_attributes")
        and bool(os.stat(path).st_file_attributes & stat.FILE_ATTRIBUTE_READONLY)
    )
    if was_readonly:
        os.chmod(path, stat.S_IWRITE)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(payload)
    os.replace(tmp, path)
    if was_readonly:
        os.chmod(path, stat.S_IREAD)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="漂移检测（CI 面）")
    mode.add_argument("--write", action="store_true", help="重录入库")
    args = parser.parse_args()

    if not _GOLDEN_PROJECT.is_file() or not _GOLDEN_EXPECTED.is_file():
        print(
            f"[FAIL] golden 案例件缺失：{_GOLDEN_PROJECT} / {_GOLDEN_EXPECTED}",
            file=sys.stderr,
        )
        return 2

    first_result, first_diag, first_sample = _build_artifacts()
    second_result, second_diag, second_sample = _build_artifacts()
    if (
        first_result != second_result
        or first_diag != second_diag
        or first_sample != second_sample
    ):
        print(
            "[FAIL] 双跑字节不一致（确定性破坏——serialize 面回归，"
            "分诊 GR-04/16/18 迭代序纪律）",
            file=sys.stderr,
        )
        return 2

    if args.write:
        _SNAP_DIR.mkdir(parents=True, exist_ok=True)
        _write_atomic(_RESULT_OUT, first_result)
        _write_atomic(_DIAG_OUT, first_diag)
        _write_atomic(_SAMPLE_OUT, first_sample)
        print(
            f"[OK] 重录入库：{_RESULT_OUT.name} {len(first_result)} 字节 + "
            f"{_DIAG_OUT.name} {len(first_diag)} 字节 + "
            f"{_SAMPLE_OUT.name} {len(first_sample)} 字节（双跑恒等）"
        )
        return 0

    drifts: list[str] = []
    for path, fresh in (
        (_RESULT_OUT, first_result),
        (_DIAG_OUT, first_diag),
        (_SAMPLE_OUT, first_sample),
    ):
        if not path.is_file():
            drifts.append(f"{path.name}：入库件缺失（先跑 --write）")
        elif path.read_bytes() != fresh:
            drifts.append(
                f"{path.name}：入库件与重生成不一致"
                f"（入库 {len(path.read_bytes())} 字节 vs 新 {len(fresh)} 字节）"
            )
    if drifts:
        print(
            "[FAIL] report golden 产物漂移——coefficients/模板/引擎面变更后"
            "须跑 tools/report_golden.py --write 重录（清单见 tools/report_golden.md）：\n  "
            + "\n  ".join(drifts),
            file=sys.stderr,
        )
        return 1
    print(
        f"[OK] report golden 产物零漂移（双跑恒等+入库逐字节一致："
        f"result.json {len(first_result)} 字节 / diag.json {len(first_diag)} 字节"
        f" / { _SAMPLE_OUT.name} {len(first_sample)} 字节）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

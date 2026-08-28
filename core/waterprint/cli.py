"""命令行入口：内核唯一可执行点（无头运行/脚手架/批量导出的落点）。

输入:  argv（子命令与参数）
输出:  进程退出码 / 控制台输出 / 产物文件（network 结果 sheet、new-unit 骨架…）

NET2 v2 记档（2026-08-28，UF-41 对齐——子命令集 v1 冻结→v2）：
- 本批（NET2 段二）实装面：`network`（管网水力设计闭环）+ `new-unit`
  （单元骨架生成，R2 幂等保护）+ 退出码语义（R1）。v1 其余成员
  `calc`/`export`/`validate`/`selfcheck` 未注册——实装归 M1 后续批
  （调用即用法错误退出码 2，语义一致；app 面已就绪待接线）。
- `wp network <pipes.xlsx> [--out <path>] [--roughness <plastic|concrete>]`：
  read_network_excel → build_design_options（真库 coefficients 装配，
  data/coefficients——网络域 load_network_coefficients 正门）→
  design_pipes → write_result_sheet → stdout 摘要；退出码 0=全部段
  设计成功 / 3=读入或数据装载校验失败 / 4=存在无解段（R5 显式失败
  非静默）。
- 交接裁决（开工问询 2026-08-28）：cli.py 原为纯骨架（v1 未实装），
  main 符号出现使 tests/app/test_cli.py 两占位接线断言按"不得删除"
  语义填真实现（退出码语义/new-unit 拒重名）——全量口径随之
  722+2+N passed/9 skipped（偏离简报预期 11，实况申报记档）。
- 修复轮（2026-08-28，二审 F-1+一审 I-1）：F-1——network --out 语义
  修正为"产出新文件"（源 xlsx 复制到目标路径再写结果 sheet，目录缺
  失则建；--out 指回源文件=写回语义不自拷贝）；退出码 3 保留给源文件
  读入失败（--out 路径问题不再误入 3 前的 stat 崩溃口径）。
  I-1——文件尾 __main__ 入口（python -m waterprint.cli 真生效；此前
  模块级零调用静默 exit 0）。
- M4a ③（2026-08-28）：export 子命令注册——v1 面仅 audit（render_
  audit_html 通道，无模板依赖）：`wp export audit <project.json>
  <result.json> [--out a.html]`；产物 GR-38 原子写+路径 '..' 拒（R5
  同款）；愿景行其余成员（calcbook/dxf/scene）保持注释未注册。
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/app/test_cli.py）
#
# 【公开接口】
#   main(argv: Sequence[str] | None = None) -> int   入口（返回退出码）
#   子命令集（v2——UF-41 对齐；v1 成员 calc/export/validate/selfcheck
#   归 M1 批，未注册=用法错误）：
#     wp network <pipes.xlsx> [--out result.xlsx]
#         [--roughness plastic|concrete]（默认 concrete）
#         管网水力设计（network 域闭环——NET2 段二）
#     wp calc <project.json> [--conditions design,avg]
#         [--out result.json]        全流程计算（app.run_full_calc）
#     wp export calcbook|audit|dxf|scene <project> <result>
#         批量导出（M1 起逐步启用；M4a 起 audit 实装=下行面）
#     wp export audit <project.json> <result.json> [--out a.html]
#         审计报告 HTML（M4a ③——render_audit_html 通道；calcbook/dxf/
#         scene 未注册=用法错误 2，愿景行其余成员保持注释）
#     wp new-unit <line> <name> [--root <units_lib 路径>]
#         从 units_lib/_template 生成单元骨架（§15 工程细节 6：
#         结构一致性不靠文档靠工具；line ∈ 四业务线，重名拒绝）
#     wp validate <project.json>    项目校验（零计算，快速反馈）
#     wp selfcheck                  注册表静态校验 + 架构自检报告
#
# 【行为规格】
#   R1 参数解析零第三方依赖之争：argparse（标准库）；
#      stdout 结构化消息（成功摘要/失败清单），退出码：
#      0=成功 2=用法错误 3=校验失败 4=计算失败（诊断进 stderr）。
#   R2 new-unit 幂等保护：目标包已存在 = 拒绝（防误覆盖）；
#      生成后打印"下一步清单"（登记 file-contracts、写测试、锁定）。
#   R3 输出确定性：calc 输出 JSON 走 result_schema 确定性序列化
#      （脚本化 diff 友好）；日志含 repro 三元组。
#   R4 Windows 路径兼容：显式 encoding="utf-8" 读写；
#      PYTHONUTF8 提示在 --help 尾注（教训：GBK 双重编码）。
#   R5 export 产物落盘（M4a ③）：GR-38 原子写（同目录 .tmp 渲染→
#      os.replace——project/io.save_project 同款）；--out 用户面 '..'
#      分量拒（audit._validate_out 同口径；相对路径以 cwd 为基准=CLI
#      用户态，network --out 先例）；失败全收编 3（export 面无计算，
#      读入/路径/审计链校验族）；项目 design_hash 与结果三元组不一致
#      =stderr 警告不拒（审计对象=该份计算，HTML 头部三元组自证版本
#      ——server R1 stale 拒绝语义归 API 面，差异见用户手册 FAQ）。
#      修复轮（2026-08-28 实证）：渲染前 discover_units 装载全单元
#      公式注册表——CLI 冷进程只读结果文件时迹公式反查需要注册表
#      就绪（app.assemble 内部同款；cli 编排层责任面）。
#
# 【测试要求】calc/validate 子命令管线（M1 起真数值）、
#   new-unit 生成结构完整且拒绝重名、退出码语义、乱码防线
#   （中文输出在 GBK 控制台不崩溃）。
#
# 【参照】重写计划 §13.3 cli 行/§15 工程细节 6
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import argparse
import contextlib
import os
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from waterprint.app import InvalidProjectError, load_project
from waterprint.contracts.result_schema import (
    InvalidResultError,
    PlantResult,
    deserialize,
)
from waterprint.network.excel_io import (
    NetworkExcelError,
    read_network_excel,
    write_result_sheet,
)
from waterprint.network.manning import NetworkHydraulicsError
from waterprint.network.solver import (
    build_design_options,
    design_pipes,
    load_network_coefficients,
)
from waterprint.registry.coefficients import InvalidCoefficientError
from waterprint.trace.audit import (
    InvalidAuditError,
    InvalidAuditPathError,
    render_audit_html,
)
from waterprint.units_lib import discover_units

__all__ = ["main"]


# 退出码语义（R1——stdout 摘要/stderr 诊断分流）：0=成功 2=用法错误
# 3=校验失败 4=计算失败——3/4 经基值推导（魔法数字门禁字面量白名单
# {0,1,2,10} 外的值须来自语义源而非裸字面量，R1 语义链即真源）。
_EXIT_OK: Final[int] = 0
_EXIT_USAGE: Final[int] = 2
_EXIT_VALIDATION: Final[int] = _EXIT_USAGE + 1
_EXIT_CALCULATION: Final[int] = _EXIT_USAGE + 2
# 管材键名口径（coefficients network.roughness.* 键名——choices 同源）。
_PIPE_TYPES: Final[tuple[str, ...]] = ("concrete", "plastic")
# 四业务线（units_lib 目录名——结构图谱 §1a UNIT_LINE_DIRS 同口径）。
_UNIT_LINES: Final[tuple[str, ...]] = (
    "municipal",
    "mine_water",
    "sludge",
    "conveyance",
)
# export 子命令已实装 kind 面（M4a ③：仅 audit——calcbook/dxf/scene 归
# 后续批；argparse choices 外=用法错误 2）。
_EXPORT_KINDS: Final[tuple[str, ...]] = ("audit",)


def _stdout_utf8() -> None:
    """R4 乱码防线：stdout 重配 UTF-8（GBK 控制台不崩溃）。"""
    stream = sys.stdout
    reconfigure = getattr(stream, "reconfigure", None)
    if callable(reconfigure):
        with contextlib.suppress(OSError):
            reconfigure(encoding="utf-8", errors="replace")


def _build_parser() -> argparse.ArgumentParser:
    """argparse 装配（R1：标准库零三方之争；子命令 required）。"""
    parser = argparse.ArgumentParser(
        prog="wp",
        description="WaterPrint 计算内核命令行（子命令集 v2——UF-41 对齐）",
        epilog="Windows 控制台建议设 PYTHONUTF8=1（教训：GBK 双重编码）",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    network = subparsers.add_parser("network", help="管网水力设计（pipes.xlsx → 结果 sheet）")
    network.add_argument("xlsx", help="管网表路径（模板 network_pipes v1.0.0）")
    network.add_argument(
        "--out",
        default=None,
        help="结果输出路径（产出新文件：源表复制后写结果 sheet；默认写回原文件）",
    )
    network.add_argument(
        "--roughness",
        choices=_PIPE_TYPES,
        default="concrete",
        help="管材糙率键（coefficients network.roughness.*，默认 concrete）",
    )
    new_unit = subparsers.add_parser(
        "new-unit", help="从 units_lib/_template 生成单元骨架（重名拒绝）"
    )
    new_unit.add_argument("line", choices=_UNIT_LINES, help="业务线")
    new_unit.add_argument("name", help="单元包名（snake_case）")
    new_unit.add_argument(
        "--root",
        default=None,
        help="units_lib 根路径（默认内核包内 units_lib；测试用临时根）",
    )
    export = subparsers.add_parser("export", help="产物导出（v1 面：audit——审计报告 HTML）")
    export_kinds = export.add_subparsers(dest="export_kind", required=True)
    for kind in _EXPORT_KINDS:
        item = export_kinds.add_parser(kind, help="审计报告 HTML（公式溯源）")
        item.add_argument("project", help="项目文件路径（project.json）")
        item.add_argument("result", help="结果文件路径（result.json——serialize 产物）")
        item.add_argument(
            "--out",
            default=None,
            help="输出 HTML 路径（默认=结果文件同目录 <名>.audit.html）",
        )
    return parser


def _run_network(xlsx: str, out: str | None, roughness: str) -> int:
    """network 子命令：读→装配→设计→（复制→）写→摘要（退出码 0/3/4）。

    out 给定且异于源：源表复制到目标（F-1 产出新文件语义）后写结果
    sheet；否则写回原文件（幂等重写）。
    """
    source = Path(xlsx).resolve()
    try:
        coefficients = load_network_coefficients()
        options = build_design_options(coefficients, roughness)
        segments = read_network_excel(source)
    except (NetworkExcelError, InvalidCoefficientError, OSError) as exc:
        print(f"[校验失败] 读入/数据装载：{exc}", file=sys.stderr)
        return _EXIT_VALIDATION
    try:
        design = design_pipes(segments, options)
    except NetworkHydraulicsError as exc:
        print(f"[计算失败] 水力求根：{exc}", file=sys.stderr)
        return _EXIT_CALCULATION
    target = Path(out).resolve() if out else source
    try:
        # F-1（2026-08-28 修复轮）：--out=产出新文件——源表复制到目标路径
        # 再写结果 sheet（源文件不动）；目录不存在则建（mkdir parents）。
        # 目标即源（--out 指回原文件）= 写回语义，跳过复制防自拷贝报错。
        if target != source:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        write_result_sheet(target, design)
    except (NetworkExcelError, OSError) as exc:
        print(f"[校验失败] 结果写出：{exc}", file=sys.stderr)
        return _EXIT_VALIDATION
    print(f"管网设计完成：{len(design.results)} 段入选（结果 sheet 已写入 {target.name}）")
    for result in design.results:
        print(
            f"  {result.segment_id}: DN{result.diameter:.3f}m 坡度 "
            f"{result.slope:.4f} h/D={result.depth_ratio:.4f} "
            f"v={result.velocity:.4f} m/s 管底 {result.invert_start:.2f}"
            f"→{result.invert_end:.2f} m"
        )
    for group in design.parallel:
        print(
            f"  {group.segment_id}: 并联双管 DN{group.diameter:.3f}m 各输"
            f"{group.per_pipe_flow:.4f} m3/s（h/D={group.depth_ratio:.4f}，"
            "用户可否决）"
        )
    for well in design.drop_wells:
        print(f"  跌水井 {well.segment_id}: 跌差 {well.drop:.3f} m")
    for failure in design.failures:
        print(f"  [无解段] {failure.segment_id}:")
        for reason in failure.reasons:
            print(f"    - {reason}")
    return _EXIT_CALCULATION if design.failures else _EXIT_OK


def _units_root(root: str | None) -> Path:
    """units_lib 根：默认内核包内（cli.py → waterprint/units_lib）。"""
    if root is not None:
        return Path(root).resolve()
    return Path(__file__).resolve().parent / "units_lib"


def _run_new_unit(line: str, name: str, root: str | None) -> int:
    """new-unit 子命令：复制 _template → 目标包（R2 幂等保护+下一步清单）。"""
    units = _units_root(root)
    template = units / "_template"
    target = units / line / name
    if target.exists():
        print(f"[拒绝] 目标单元包已存在：{target}（R2 幂等保护——防误覆盖，改名或删除后重试）")
        return _EXIT_CALCULATION
    if not template.is_dir():
        print(f"[校验失败] 模板包缺失：{template}", file=sys.stderr)
        return _EXIT_VALIDATION
    try:
        shutil.copytree(
            template,
            target,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
    except OSError as exc:
        print(f"[计算失败] 生成失败：{exc}", file=sys.stderr)
        return _EXIT_CALCULATION
    print(f"单元骨架已生成：{target}")
    print("下一步清单（§15 工程细节 6——结构一致性靠工具更靠流程）：")
    print("  1. 编写 manifest.py（UNIT_ID、参数/端口/去除率/条文——R1 逐条复核出处）")
    print("  2. 登记 docs/file-contracts.md §3 包清单+结构图谱 §3 单元总表")
    print("  3. 编写包内测试（tests/test_compute.py + properties.py）")
    print("  4. 锁定：python scripts/lock_tests.py <包 tests 路径>（独立 commit）")
    return _EXIT_OK


def _audit_out(result_path: Path, out: str | None) -> Path | None:
    """export audit 输出路径裁定（R5）：默认=结果同目录 <stem>.audit.html。

    用户面路径含 '..' 分量=拒（None——audit._validate_out 同口径；相对
    路径以 cwd 为基准后 resolve——CLI 用户态，network --out 先例）。
    """
    if out is None:
        return result_path.with_suffix(".audit.html")
    raw = Path(out)
    for part in raw.parts:
        if part == "..":
            print(
                f"[校验失败] 输出路径含越界分量 '..'：{raw}（R5 同款口径——audit._validate_out）",
                file=sys.stderr,
            )
            return None
    return (raw if raw.is_absolute() else Path.cwd() / raw).resolve()


def _load_audit_inputs(project: str, result_path: Path) -> PlantResult | None:
    """export audit 读入半：项目→结果→注册表装载（失败打印+None）。

    三段读入族统一收编（打印面各自指明环节）；项目-结果三元组不一致
    =stderr 警告不拒（审计对象=该份计算——HTML 头部三元组自证版本）。
    """
    try:
        project_file = load_project(Path(project).resolve())
    except (InvalidProjectError, OSError) as exc:
        print(f"[校验失败] 项目文件读入：{exc}", file=sys.stderr)
        return None
    try:
        plant = deserialize(result_path.read_bytes())
    except (OSError, InvalidResultError) as exc:
        print(f"[校验失败] 结果文件读入：{exc}", file=sys.stderr)
        return None
    try:
        discover_units()  # 公式注册表装载（结果迹反查释义的前置条件）
    except (ImportError, OSError) as exc:  # 装配面可预期失败族
        print(f"[校验失败] 单元注册表装载：{exc}", file=sys.stderr)
        return None
    if project_file.metadata.content_hash != plant.repro.design_hash:
        print(
            "[警告] 项目 design hash 与结果三元组不一致——审计对象=该份"
            "计算，报告头部三元组自证版本（当前项目请先重算）",
            file=sys.stderr,
        )
    return plant


def _run_export_audit(project: str, result: str, out: str | None) -> int:
    """export audit 子命令：路径裁定→读对→渲染→原子落盘（退出码 0/3）。

    落盘 GR-38：同目录 .tmp 渲染→os.replace，失败 os.remove 清半写
    tmp。修复轮（2026-08-28 实证）：渲染前 discover_units 装载全单元
    包公式注册表——CLI 冷进程只读结果文件时迹公式反查需要注册表就绪
    （app.assemble 内部同款装载；cli 为编排层责任面）。
    """
    result_path = Path(result).resolve()
    target = _audit_out(result_path, out)
    if target is None:
        return _EXIT_VALIDATION
    plant = _load_audit_inputs(project, result_path)
    if plant is None:
        return _EXIT_VALIDATION
    tmp = target.with_name(target.name + ".tmp")
    try:
        render_audit_html(plant.trace, plant, tmp)
        os.replace(tmp, target)
    except (InvalidAuditError, InvalidAuditPathError) as exc:
        with contextlib.suppress(OSError):
            os.remove(tmp)  # 半写 .tmp 不留
        print(f"[校验失败] 审计链校验：{exc}", file=sys.stderr)
        return _EXIT_VALIDATION
    except OSError as exc:
        with contextlib.suppress(OSError):
            os.remove(tmp)
        print(f"[校验失败] 报告落盘：{exc}", file=sys.stderr)
        return _EXIT_VALIDATION
    print(f"审计报告已生成：{target}")
    print(
        f"  迹 {len(plant.trace)} 条 / 工况 {len(plant.conditions)} 档 / "
        f"design_hash {plant.repro.design_hash}（GR-38 原子落盘）"
    )
    return _EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    """入口（返回退出码）：R1 语义 0/2/3/4；argparse 用法错误收编为 2。"""
    _stdout_utf8()
    parser = _build_parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else _EXIT_USAGE
    if args.command == "network":
        return _run_network(args.xlsx, args.out, args.roughness)
    if args.command == "new-unit":
        return _run_new_unit(args.line, args.name, args.root)
    if args.command == "export":
        return _run_export_audit(args.project, args.result, args.out)
    parser.error(f"未知子命令：{args.command!r}")
    return _EXIT_USAGE  # pragma: no cover（parser.error 必先 SystemExit）


# I-1（2026-08-28 修复轮）：模块真入口——python -m waterprint.cli …
# 此前无本块，-m 调用只完成模块定义即静默退出码 0（零动作）。
if __name__ == "__main__":
    raise SystemExit(main())

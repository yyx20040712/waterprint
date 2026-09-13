"""命令行入口：内核唯一可执行点（无头运行/脚手架/批量导出的落点）。

输入:  argv（子命令与参数）
输出:  进程退出码 / 控制台输出 / 产物文件（network 结果 sheet、new-unit 骨架…）

记档（NET2 v2 2026-08-28 UF-41 子命令集 v1→v2：段二实装 network+new-unit
+退出码语义 R1；交接裁决=main 符号使 test_cli.py 占位断言按"不得删除"
语义填真实现[全量口径 722+2+N passed/9 skipped 实况申报]；修复轮 F-1=
network --out 产出新文件语义[源表复制后写结果 sheet，指回源=写回不自
拷贝]、I-1=__main__ 真入口；M4a ③=export audit 实装[render_audit_html
通道，GR-38 原子写+'..' 拒 R5]，愿景行其余成员保持注释未注册）。
AI1 轨道甲（2026-09-13，M1 旧账清）：注册 calc/validate/export
calcbook/export dxf/selfcheck 五成员——编排全部转调 waterprint.flows
（用例流层——任务书 §3 冻结签名）；export audit 同批收编 flows.
export_flow("audit")（渲染/原子写单一真源=flows.audit_render_flow，
读入半[项目→结果→注册表装载→hash 警告]留壳）；calc=flows 全链
（--conditions=受检单元逗号清单，缺省=仅基线 design/avg 两档——server/
worker 同语义）；validate=结构校验清单式（有错=3——⑦甲呈报不拒协调）；
export dxf --site=site_design 取 project.design.site（M5 总图通道）；
selfcheck=discover_units 装载报告+manifest 计数（core 无现成函数——
任务书预案口径）；export scene 保持未注册（2）。退出码 0/2/3/4 语义
不变（T5 读码回填：3=读入/守护/装配校验族，4=执行期领域异常族——
calc 面 _CALC_* 声明面）。
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（镜像测试 tests/app/test_cli.py）
#
# 【公开接口】
#   main(argv: Sequence[str] | None = None) -> int   入口（返回退出码）
#   子命令集（v2 补全=AI1 轨道甲；v1 成员全部实装）：
#     wp network <pipes.xlsx> [--out result.xlsx] [--roughness plastic|concrete]
#     wp calc <project.json> [--conditions aao,cass] [--data-dir <path>]
#         [--out result.json]（--out 缺省=项目同目录 <stem>.result.json）
#     wp validate <project.json>（零计算清单式——有错退出码 3）
#     wp export audit <project.json> <result.json> [--out a.html]
#     wp export calcbook <project> <result> [--out x.xlsx] [--data-dir]
#     wp export dxf <project> <result> [--out d.dxf] [--data-dir]
#         [--unit-id] [--condition-key] [--sheet profile] [--site]
#     wp new-unit <line> <name> [--root <units_lib 路径>]（重名拒绝 R2）
#     wp selfcheck（注册表静态校验报告——装载+manifest 计数）
#     愿景行其余成员（export scene）保持注释未注册（用法错误 2）。
#
# 【行为规格】
#   R1 argparse（标准库）；stdout 结构化消息，退出码 0=成功 2=用法错误
#      3=校验失败 4=计算失败（诊断进 stderr；3/4 经基值推导——字面量
#      白名单 {0,1,2,10} 外须来自语义源，R1 语义链即真源）。
#   R2 new-unit 幂等保护：目标包已存在=拒绝；生成后打印"下一步清单"。
#   R3 calc 输出走 result_schema 确定性序列化（脚本化 diff 友好）。
#   R4 Windows 兼容：显式 encoding="utf-8" 读写；--help 尾注 PYTHONUTF8。
#   R5 export 产物落盘：GR-38 原子写（audit 单一真源=flows.
#      audit_render_flow；calcbook/dxf 由 export_artifact 内部落盘）；
#      --out 用户面 '..' 分量拒（_user_out 共用——audit._validate_out
#      同口径；相对路径以 cwd 基准=CLI 用户态）；export 面失败全收编 3
#      （读入/模板/路径/审计链族）；design_hash 与结果三元组不一致=
#      stderr 警告不拒；渲染前 discover_units 装载注册表（迹公式反查
#      前置——app.assemble 同款，2026-08-28 实证）。
#   R6 calc 装配链（AI1）：flows.build_env_flow（--data-dir 缺省=仓库根
#      data）→build_condition_flow→build_standards_flow（缺失宽容警告）→
#      run_calc_flow；异常族 _CALC_VALIDATIONS→3 / _CALC_FAILURES→4。
#
# 【测试要求】退出码语义、new-unit 拒重名、calc/validate/calcbook/dxf/
#   selfcheck 端到端（golden municipal 实跑）、乱码防线（GBK 不崩溃）。
# 【参照】重写计划 §13.3 cli 行/§15 工程细节 6；AI1 路线设计书 v2 D6
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import argparse
import contextlib
import shutil
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Final

from waterprint import flows
from waterprint.app import (  # app 门面（UF-33 单入口）
    ArtifactKindNotReady,
    InvalidAssemblyError,
    InvalidProjectError,
    load_project,
)
from waterprint.contracts.manifest import InvalidUnitConfig
from waterprint.contracts.ports import InvalidConnection
from waterprint.contracts.project_schema import ProjectFile
from waterprint.contracts.result_schema import InvalidResultError, PlantResult, deserialize
from waterprint.graph import LoopDivergence
from waterprint.graph.executor_dsl import InvalidExecutionError
from waterprint.graph.nodes import InvalidNodeError
from waterprint.network.excel_io import NetworkExcelError, read_network_excel, write_result_sheet
from waterprint.network.manning import NetworkHydraulicsError
from waterprint.network.solver import build_design_options, design_pipes, load_network_coefficients
from waterprint.registry.coefficients import InvalidCoefficientError
from waterprint.trace.audit import InvalidAuditError, InvalidAuditPathError
from waterprint.trace.calcbook import InvalidTemplateError
from waterprint.units_lib import discover_units

__all__ = ["main"]

# 退出码语义（R1）：0=成功 2=用法错误 3=校验失败 4=计算失败。
_EXIT_OK: Final[int] = 0
_EXIT_USAGE: Final[int] = 2
_EXIT_VALIDATION: Final[int] = _EXIT_USAGE + 1
_EXIT_CALCULATION: Final[int] = _EXIT_USAGE + 2
# 管材键名口径（coefficients network.roughness.*——choices 同源）。
_PIPE_TYPES: Final[tuple[str, ...]] = ("concrete", "plastic")
# 四业务线（units_lib 目录名——结构图谱 §1a 同口径）。
_UNIT_LINES: Final[tuple[str, ...]] = ("municipal", "mine_water", "sludge", "conveyance")
# 数据包根缺省（仓库根 data——golden 测试同款 parents 解析）。
_DATA_DIR_DEFAULT: Final[Path] = Path(__file__).resolve().parents[2] / "data"
# calc 面 3 族（读入/守护/装配校验）与 4 族（执行期领域异常）——R6。
_CALC_VALIDATIONS: Final[tuple[type[BaseException], ...]] = (
    InvalidProjectError, InvalidAssemblyError, InvalidCoefficientError,
    flows.InvalidFlowError, OSError,
)
_CALC_FAILURES: Final[tuple[type[BaseException], ...]] = (
    LoopDivergence, InvalidNodeError, InvalidConnection,
    InvalidUnitConfig, InvalidExecutionError,
)
# export 面失败收编族（无计算——R5 全收 3）。
_EXPORT_FAILURES: Final[tuple[type[BaseException], ...]] = (
    ArtifactKindNotReady, InvalidTemplateError, InvalidAuditError,
    InvalidAuditPathError, flows.InvalidFlowError, OSError,
)


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
        description="WaterPrint 计算内核命令行（子命令集 v2 补全——AI1 轨道甲）",
        epilog="Windows 控制台建议设 PYTHONUTF8=1（教训：GBK 双重编码）",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    network = subparsers.add_parser("network", help="管网水力设计（pipes.xlsx → 结果 sheet）")
    network.add_argument("xlsx", help="管网表路径（模板 network_pipes v1.0.0）")
    network.add_argument("--out", default=None,
                         help="结果输出路径（产出新文件；默认写回原文件）")
    network.add_argument("--roughness", choices=_PIPE_TYPES, default="concrete",
                         help="管材糙率键（默认 concrete）")
    new_unit = subparsers.add_parser("new-unit",
                                     help="从 units_lib/_template 生成单元骨架（重名拒绝）")
    new_unit.add_argument("line", choices=_UNIT_LINES, help="业务线")
    new_unit.add_argument("name", help="单元包名（snake_case）")
    new_unit.add_argument("--root", default=None,
                          help="units_lib 根路径（默认内核包内；测试用临时根）")
    calc = subparsers.add_parser("calc", help="全流程计算（flows 全链——结果 JSON 落盘）")
    calc.add_argument("project", help="项目文件路径（project.json）")
    calc.add_argument("--conditions", default=None,
                      help="受检单元逗号清单（缺省=基线 design/avg 两档）")
    calc.add_argument("--data-dir", default=None, help="数据包根（默认仓库 data/）")
    calc.add_argument("--out", default=None,
                      help="结果输出路径（默认=项目同目录 <stem>.result.json）")
    validate = subparsers.add_parser("validate", help="设计结构校验（零计算清单式——有错退出码 3）")
    validate.add_argument("project", help="项目文件路径（project.json）")
    subparsers.add_parser("selfcheck", help="注册表静态校验报告（装载报告+manifest 计数）")
    export = subparsers.add_parser("export", help="产物导出（audit/calcbook/dxf——scene 归后续批）")
    export_kinds = export.add_subparsers(dest="export_kind", required=True)
    audit = export_kinds.add_parser("audit", help="审计报告 HTML（公式溯源）")
    audit.add_argument("project", help="项目文件路径（project.json）")
    audit.add_argument("result", help="结果文件路径（serialize 产物）")
    audit.add_argument("--out", default=None,
                       help="输出 HTML 路径（默认=结果同目录 <名>.audit.html）")
    calcbook = export_kinds.add_parser("calcbook", help="计算书 xlsx（正式模板渲染）")
    calcbook.add_argument("project", help="项目文件路径（project.json）")
    calcbook.add_argument("result", help="结果文件路径（serialize 产物）")
    calcbook.add_argument("--out", default=None,
                          help="输出 xlsx 路径（默认=结果同目录 <名>.calcbook.xlsx）")
    calcbook.add_argument("--data-dir", default=None, help="数据包根（默认仓库 data/）")
    dxf = export_kinds.add_parser("dxf", help="DXF 图纸（单单元/总图[--site]/纵断）")
    dxf.add_argument("project", help="项目文件路径（project.json）")
    dxf.add_argument("result", help="结果文件路径（serialize 产物）")
    dxf.add_argument("--out", default=None, help="输出 DXF 路径（默认=结果同目录 <名>.dxf）")
    dxf.add_argument("--data-dir", default=None, help="数据包根（默认仓库 data/）")
    dxf.add_argument("--unit-id", default=None, help="单单元出图目标（缺省=总图须 --site）")
    dxf.add_argument("--condition-key", default=None, help="出图工况（缺省=首档+警告）")
    dxf.add_argument("--sheet", choices=("profile",), default=None, help="图纸形态（纵断）")
    dxf.add_argument("--site", action="store_true", help="全厂总图（site=project.design.site——M5）")
    return parser


def _run_network(xlsx: str, out: str | None, roughness: str) -> int:
    """network 子命令：读→装配→设计→（复制→）写→摘要（0/3/4；F-1 语义）。"""
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
        if target != source:  # F-1：--out=产出新文件（目录缺失则建；指回源=写回不自拷贝）
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        write_result_sheet(target, design)
    except (NetworkExcelError, OSError) as exc:
        print(f"[校验失败] 结果写出：{exc}", file=sys.stderr)
        return _EXIT_VALIDATION
    print(f"管网设计完成：{len(design.results)} 段入选（结果 sheet 已写入 {target.name}）")
    for result in design.results:
        print(f"  {result.segment_id}: DN{result.diameter:.3f}m 坡度 {result.slope:.4f} "
              f"h/D={result.depth_ratio:.4f} v={result.velocity:.4f} m/s 管底 "
              f"{result.invert_start:.2f}→{result.invert_end:.2f} m")
    for group in design.parallel:
        print(f"  {group.segment_id}: 并联双管 DN{group.diameter:.3f}m 各输"
              f"{group.per_pipe_flow:.4f} m3/s（h/D={group.depth_ratio:.4f}，用户可否决）")
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
            template, target,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
    except OSError as exc:
        print(f"[计算失败] 生成失败：{exc}", file=sys.stderr)
        return _EXIT_CALCULATION
    print(f"单元骨架已生成：{target}")
    print("下一步清单（§15 工程细节 6——结构一致性靠工具更靠流程）：")
    print("  1. 编写 manifest.py（UNIT_ID、参数/端口/去除率/条文——R1 逐条复核出处）")
    print("  2. 登记 file-contracts.md §3+结构图谱 §3 单元总表")
    print("  3. 编写包内测试（tests/test_compute.py + properties.py）")
    print("  4. 锁定：python scripts/lock_tests.py <包 tests 路径>（独立 commit）")
    return _EXIT_OK


def _user_out(out: str | None, default: Path) -> Path | None:
    """用户面输出路径裁定（R5 共用）：'..' 分量拒；相对路径以 cwd 为基准。"""
    if out is None:
        return default
    raw = Path(out)
    for part in raw.parts:
        if part == "..":
            print(f"[校验失败] 输出路径含越界分量 '..'：{raw}"
                  "（R5 同款口径——audit._validate_out）", file=sys.stderr)
            return None
    return (raw if raw.is_absolute() else Path.cwd() / raw).resolve()


def _data_dir(raw: str | None) -> Path:
    """数据包根裁定：--data-dir 给定用之；缺省=仓库根 data（golden 同款）。"""
    return Path(raw).resolve() if raw is not None else _DATA_DIR_DEFAULT


def _load_pair(project: str, result_path: Path) -> tuple[ProjectFile, PlantResult] | None:
    """export 面读入半（三 kind 共用）：项目→结果→注册表装载→hash 警告。

    三段读入族统一收编；三元组不一致=stderr 警告不拒（审计对象=该份
    计算——HTML 头部三元组自证版本）。"""
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
        print("[警告] 项目 design hash 与结果三元组不一致——审计对象=该份"
              "计算，报告头部三元组自证版本（当前项目请先重算）", file=sys.stderr)
    return project_file, plant


def _run_export_audit(project: str, result: str, out: str | None) -> int:
    """export audit：路径裁定→读对→flows 渲染原子落盘（0/3）。

    AI1 轨道甲起渲染/原子写转调 flows.export_flow("audit")（单一真源=
    flows.audit_render_flow——GR-38；cli 保留读入半与退出码面）。"""
    result_path = Path(result).resolve()
    target = _user_out(out, result_path.with_suffix(".audit.html"))
    if target is None:
        return _EXIT_VALIDATION
    loaded = _load_pair(project, result_path)
    if loaded is None:
        return _EXIT_VALIDATION
    project_file, plant = loaded
    try:
        path = flows.export_flow(
            "audit", project_file, plant, template_dir=_DATA_DIR_DEFAULT, out=target
        )
    except _EXPORT_FAILURES as exc:
        print(f"[校验失败] 审计链校验：{exc}", file=sys.stderr)
        return _EXIT_VALIDATION
    print(f"审计报告已生成：{path}")
    print(f"  迹 {len(plant.trace)} 条 / 工况 {len(plant.conditions)} 档 / "
          f"design_hash {plant.repro.design_hash}（GR-38 原子落盘）")
    return _EXIT_OK


def _run_calc(project_path: str, conditions: str | None,
              data_dir: str | None, out: str | None) -> int:
    """calc：flows 全链 → stdout 六指标摘要+warnings 计数+digest（0/3/4）。"""
    source = Path(project_path).resolve()
    target = _user_out(out, source.with_suffix(".result.json"))
    if target is None:
        return _EXIT_VALIDATION
    keys = None if conditions is None else [k for k in conditions.split(",") if k]
    pack = _data_dir(data_dir)
    try:
        project = load_project(source)
        env = flows.build_env_flow(pack, project)
        cond = flows.build_condition_flow(project, keys)
        standards = flows.build_standards_flow(pack)
        result = flows.run_calc_flow(project, cond, env, standards, result_out=target)
    except _CALC_VALIDATIONS as exc:
        print(f"[校验失败] 读入/装配/守护：{exc}", file=sys.stderr)
        return _EXIT_VALIDATION
    except _CALC_FAILURES as exc:
        print(f"[计算失败] 执行期：{exc}", file=sys.stderr)
        return _EXIT_CALCULATION
    warns = sum(
        len(unit.warnings)
        for snapshot in result.plant.conditions.values()
        for unit in snapshot.values()
    )
    print(
        f"计算完成：{len(result.plant.conditions)} 工况 / warnings {warns} 条 / "
        f"design_digest {result.design_digest}"
    )
    for condition_key in result.plant.conditions:
        summary = result.plant.summary.get(condition_key, {})
        line = "  ".join(f"{k}={v:.6g}" for k, v in summary.items())
        print(f"  [{condition_key}] {line or '（无水质键——非市政终水口径）'}")
    print(f"  结果已写入 {result.result_path}（serialize 确定性——GR-38 原子落盘）")
    return _EXIT_OK


def _run_validate(project_path: str) -> int:
    """validate：结构校验清单打印（零计算；有错=3——⑦甲协调）。"""
    try:
        project = load_project(Path(project_path).resolve())
        errors = flows.validate_flow(project)
    except (InvalidProjectError, OSError) as exc:
        print(f"[校验失败] 项目文件读入：{exc}", file=sys.stderr)
        return _EXIT_VALIDATION
    if errors:
        print(f"结构校验：{len(errors)} 处错误")
        for item in errors:
            print(f"  - {item}")
        return _EXIT_VALIDATION
    print("结构校验通过：0 错误（边端点/端口在册/方向流体三查全过）")
    return _EXIT_OK


def _run_export_calcbook(project: str, result: str, out: str | None,
                         data_dir: str | None) -> int:
    """export calcbook：正式模板渲染（0/3——export 面失败收编 3）。"""
    result_path = Path(result).resolve()
    target = _user_out(out, result_path.with_suffix(".calcbook.xlsx"))
    if target is None:
        return _EXIT_VALIDATION
    loaded = _load_pair(project, result_path)
    if loaded is None:
        return _EXIT_VALIDATION
    project_file, plant = loaded
    try:
        path = flows.export_flow(
            "calcbook", project_file, plant,
            template_dir=_data_dir(data_dir) / "templates", out=target,
        )
    except _EXPORT_FAILURES as exc:
        print(f"[校验失败] calcbook 导出链：{exc}", file=sys.stderr)
        return _EXIT_VALIDATION
    print(f"计算书已生成：{path}（正式模板——占位符全展开）")
    return _EXIT_OK


def _run_export_dxf(  # noqa: PLR0913, PLR0917  # 选项透传面（app_export._export_dxf 行内豁免同款先例）
    project: str, result: str, out: str | None, data_dir: str | None,
    unit_id: str | None, condition_key: str | None, sheet: str | None, site: bool,
) -> int:
    """export dxf：单单元/总图/纵断路由（0/3——M5 --site 通道）。"""
    result_path = Path(result).resolve()
    target = _user_out(out, result_path.with_suffix(".dxf"))
    if target is None:
        return _EXIT_VALIDATION
    loaded = _load_pair(project, result_path)
    if loaded is None:
        return _EXIT_VALIDATION
    project_file, plant = loaded
    try:
        path = flows.export_flow(
            "dxf", project_file, plant,
            template_dir=_data_dir(data_dir) / "templates", out=target,
            unit_id=unit_id, condition_key=condition_key, sheet=sheet,
            site_design=project_file.design.site if site else None,
        )
    except _EXPORT_FAILURES as exc:
        print(f"[校验失败] dxf 导出链：{exc}", file=sys.stderr)
        return _EXIT_VALIDATION
    print(f"DXF 图纸已生成：{path}（工况 {condition_key or '首档'}）")
    return _EXIT_OK


def _run_selfcheck() -> int:
    """selfcheck：注册表装载报告+manifest 计数（静态零计算——任务书预案）。"""
    try:
        discovered = discover_units()
    except (ImportError, OSError) as exc:
        print(f"[校验失败] 单元注册表装载：{exc}", file=sys.stderr)
        return _EXIT_VALIDATION
    print(f"注册表装载：{len(discovered)} 单元包（重复 unit_id 启动期拒——铁律）")
    params_total = 0
    ports_total = 0
    for unit_id in sorted(discovered):
        manifest = discovered[unit_id][0]
        params_total += len(manifest.params)
        ports_total += len(manifest.ports)
        print(f"  {unit_id}: 参数 {len(manifest.params)} / 端口 {len(manifest.ports)}"
              f" / 去除率引用 {len(manifest.removal_refs)}")
    print(f"合计：manifest 参数 {params_total} 条 / 端口 {ports_total} 条")
    return _EXIT_OK


def _dispatch(args: argparse.Namespace) -> int:
    """子命令分发表（argparse dest 面——表驱动防 if/return 链膨胀）。"""
    table: dict[str, Callable[[], int]] = {
        "network": lambda: _run_network(args.xlsx, args.out, args.roughness),
        "new-unit": lambda: _run_new_unit(args.line, args.name, args.root),
        "calc": lambda: _run_calc(
            args.project, args.conditions, args.data_dir, args.out),
        "validate": lambda: _run_validate(args.project),
        "selfcheck": _run_selfcheck,
    }
    runner = table.get(args.command)
    if runner is not None:
        return runner()
    if args.command != "export":  # pragma: no cover（subparsers required 面内）
        raise SystemExit(_EXIT_USAGE)
    if args.export_kind == "audit":
        return _run_export_audit(args.project, args.result, args.out)
    if args.export_kind == "calcbook":
        return _run_export_calcbook(args.project, args.result, args.out, args.data_dir)
    return _run_export_dxf(args.project, args.result, args.out, args.data_dir,
                           args.unit_id, args.condition_key, args.sheet, args.site)


def main(argv: Sequence[str] | None = None) -> int:
    """入口（返回退出码）：R1 语义 0/2/3/4；argparse 用法错误收编为 2。"""
    _stdout_utf8()
    parser = _build_parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else _EXIT_USAGE
    return _dispatch(args)


# I-1（2026-08-28 修复轮）：模块真入口——python -m waterprint.cli …
if __name__ == "__main__":
    raise SystemExit(main())

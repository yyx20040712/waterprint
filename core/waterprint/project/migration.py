"""format_version 迁移链：旧版项目 JSON → 当前版对象（链式、可测试）。

输入:  任意历史 format_version 的项目 JSON
输出:  当前版 ProjectFile（迁移路径记录进 metadata.migrated_from）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T7a 实现 D6 裁决 2026-08-25；镜像测试 tests/project/test_migration.py）
#
# 【公开接口】
#   SUPPORTED_VERSIONS: Final[tuple[str, ...]] = ("1.0",)
#       迁移链覆盖的版本序列（链尾=当前版，锁定用例 [-1]=="1.0"）；
#       产品首发无历史版本——链框架就位未来只增。
#   migrate(data: Mapping[str, Any]) -> ProjectFile   自动识别版本迁移
#
# 【行为规格】
#   R1 链式迁移：v(n)→v(n+1) 每步一个纯函数迁移器，注册进
#      _MIGRATIONS（链式迁移器注册表）；任意旧版经链到达当前版；
#      跳级 = 链式复合，禁止写 n→current 的快捷迁移（组合爆炸与
#      漏网）。【T7a 注记】v1 零历史版本——_MIGRATIONS 为空框架
#      就位，未来版本增量只在此追加 (源版, 目标版, 迁移器) 条目。
#   R2 迁移器纯函数 + 显式记录：每步迁移写入迁移日志（结构=经过
#      版本链与字段增删改列表），进 metadata.migrated_from（审计
#      可见）；不可迁移的字段（语义不明）抛领域异常并指明字段路径
#      ——禁止猜测性默认。【T7a 注记】v1 无历史迁移——日志结构经
#      Metadata.migrated_from 字段（GR-21 只增，T7a commit① 落地）
#      就位、恒 None；"未知旧字段样本"以未知历史版本拒语义落（D8）。
#   R3 未来版本（format_version > 当前）→ InvalidProjectError 明确
#      拒绝（不降级打开，防静默丢数据；消息含两版本）。
#   R4 每个迁移器配 golden 用例：旧版样本 → 迁移后断言（样本文件进
#      core/tests/golden/golden_data/migrations/，由人类维护）。
#      【T7a 注记】v1 零迁移器=零 golden 样本义务。
#   R5 M4 旧系统导入器（best-effort）是独立入口（app.py 编排），
#      不混入本迁移链（旧格式非本产品版本史）。
#
# 【T7a 冻结注记】
#   - 版本识别序：=="1.0" 直通（零迁移，migrated_from 不动）→ 数值
#     序大于当前版 → 未来版拒；其余（含非数值格式版本串）→ 未知
#     历史版本拒（消息含版本与合法序列）。
#   - migrate 复用 io.InvalidProjectError（GR-11 族不另建同义类；
#     project 包内 migration→io import 合法，§1b 零新边）；校验
#     拒绝的 ValidationError 转换与 io._build 同款消息拼接（B4
#     双胞胎，禁跨模块私有 import）。
#   - 数值纪律：本文件零数值面。
#
# 【测试要求】链式到达、逐步日志、不可迁移拒绝、未来版拒绝、
#   golden 样本往返（v1 后续版本起）。
#
# 【参照】重写计划 §7 M4/§12.3；简报 T7a D6
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Final

from pydantic import ValidationError

from waterprint.contracts.project_schema import ProjectFile, parse_project
from waterprint.project.io import InvalidProjectError

SUPPORTED_VERSIONS: Final[tuple[str, ...]] = ("1.0",)

# 链式迁移器注册表（R1）：(源版, 目标版, 迁移器) 按链序排列。
# 迁移器签名：Callable[[MutableMapping[str, Any]], None]——就地纯
# 变换数据树（无 I/O、无随机），每步完成后写入迁移日志结构。
_MIGRATIONS: Final[tuple[tuple[str, str, Callable[[Any], None]], ...]] = ()


def _version_key(version: str) -> tuple[int, ...] | None:
    """点分数值版本串 → 整数序元组（"1.0"→(1,0)）；非数值格式 → None。"""
    parts = version.split(".")
    if not parts or not all(part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def _parse(data: Mapping[str, Any]) -> ProjectFile:
    """严格校验（与 io._build 同款消息拼接，B4 双胞胎）：loc 路径进消息。"""
    try:
        return parse_project(data)
    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(str(loc) for loc in error['loc']) or '<root>'}:"
            f" {error['msg']}"
            for error in exc.errors()
        )
        raise InvalidProjectError(
            f"项目数据校验失败（strict + extra=forbid）：{details}"
        ) from exc


def migrate(data: Mapping[str, Any]) -> ProjectFile:
    """版本识别正门：当前版直通 / 未来版拒 / 未知历史版拒（R2/R3）。"""
    if not isinstance(data, Mapping):
        raise InvalidProjectError(
            f"项目数据顶层须为映射：得到 {type(data).__name__}"
            "（format_version 为顶层权威源键）"
        )
    version = data.get("format_version")
    if not isinstance(version, str) or not version:
        raise InvalidProjectError(
            f"项目数据缺顶层 format_version（权威源键，R5——迁移链只读顶层）："
            f"得到 {version!r}"
        )
    current = SUPPORTED_VERSIONS[-1]
    if version == current:
        return _parse(data)
    key, current_key = _version_key(version), _version_key(current)
    if key is not None and current_key is not None and key > current_key:
        raise InvalidProjectError(
            f"未来版本拒绝：文件 format_version={version!r} > 当前支持"
            f" {current!r}（R3——不降级打开，防静默丢数据；请升级程序）"
        )
    raise InvalidProjectError(
        f"未知历史版本：文件 format_version={version!r} 不在合法版本序列"
        f" {list(SUPPORTED_VERSIONS)} 内（v1 产品首发无历史迁移链——"
        "R1 链框架就位未来只增；来源不明文件请走 M4 旧系统导入器）"
    )

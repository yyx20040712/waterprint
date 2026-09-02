"""format_version 迁移链：旧版项目 JSON → 当前版对象（链式、可测试）。

输入:  任意历史 format_version 的项目 JSON
输出:  当前版 ProjectFile（迁移路径记录进 metadata.migrated_from）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T7a 实现 D6 裁决 2026-08-25；镜像测试 tests/project/test_migration.py）
#
# 【公开接口】
#   SUPPORTED_VERSIONS: Final[tuple[str, ...]] = ("1.0", "2.0")
#       迁移链覆盖的版本序列（链尾=当前版，锁定用例 [-1]=="2.0"）；
#       M1 批（site 键）起链启用首条 v1→v2——后续版本只增条目。
#   migrate(data: Mapping[str, Any]) -> ProjectFile   自动识别版本迁移
#
# 【行为规格】
#   R1 链式迁移：v(n)→v(n+1) 每步一个纯函数迁移器，注册进
#      _MIGRATIONS（链式迁移器注册表）；任意旧版经链到达当前版；
#      跳级 = 链式复合，禁止写 n→current 的快捷迁移（组合爆炸与
#      漏网）。【T7a→M1 注记】M1 批（site 键）启用首条 ("1.0","2.0")
#      条目——后续版本增量只在此追加 (源版, 目标版, 迁移器) 条目。
#   R2 迁移器纯函数 + 显式记录：每步迁移写入迁移日志（结构=经过
#      版本链与字段增删改列表），进 metadata.migrated_from（审计
#      可见）；不可迁移的字段（语义不明）抛领域异常并指明字段路径
#      ——禁止猜测性默认。【T7a 注记】v1 无历史迁移——日志结构经
#      Metadata.migrated_from 字段（GR-21 只增，T7a commit① 落地）
#      就位；M1 批起由链写来源版（多级跳步保留最早非空来源）；
#      "未知旧字段样本"以未知历史版本拒语义落（D8）。
#   R3 未来版本（format_version > 当前）→ InvalidProjectError 明确
#      拒绝（不降级打开，防静默丢数据；消息含两版本）。
#   R4 每个迁移器配 golden 用例：旧版样本 → 迁移后断言（样本文件进
#      core/tests/golden/golden_data/migrations/，由人类维护）。
#      【M1 注记】v1→v2 回归证据由 tests/project/test_site_migration.py
#      内置合成 fixture 承担（简报 §二.4——golden_data/migrations 不动）。
#   R5 M4 旧系统导入器（best-effort）是独立入口（app.py 编排），
#      不混入本迁移链（旧格式非本产品版本史）。
#
# 【T7a 冻结注记】
#   - 版本识别序：==当前版直通（零迁移，migrated_from 不动）→ 数值
#     序大于当前版 → 未来版拒；其余（含非数值格式版本串）→ 未知
#     历史版本拒（经 _MIGRATIONS 链，不可达即拒；消息含版本与合法序列）。
#   - migrate 复用 io.InvalidProjectError（GR-11 族不另建同义类；
#     project 包内 migration→io import 合法，§1b 零新边）；校验
#     拒绝的 ValidationError 转换与 io._build 同款消息拼接（B4
#     双胞胎，禁跨模块私有 import）。
#   - 双源同步对侧互注（T7a-R1b 2026-08-25，二审 M-2+T7aG-1 补齐）：
#     io._FORMAT_VERSION（dumps_design 版本头）与本文件
#     SUPPORTED_VERSIONS[-1] 双源同值——升版必同笔改两处（io 侧
#     规格 R6 已注，本行为对侧注记使"互注"成真；漂移后果=未来版
#     哈希失效语义静默漂移，由 migrate 未来版拒路径兜底）。
#   - 数值纪律：本文件零数值面。
#
# 【测试要求】链式到达、逐步日志、不可迁移拒绝、未来版拒绝、
#   golden 样本往返（v1 后续版本起）。
#
# 【参照】重写计划 §7 M4/§12.3；简报 T7a D6
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import copy
from collections.abc import Callable, Mapping, MutableMapping
from typing import Any, Final

from pydantic import ValidationError

from waterprint.contracts.project_schema import ProjectFile, parse_project
from waterprint.project.io import InvalidProjectError

SUPPORTED_VERSIONS: Final[tuple[str, ...]] = ("1.0", "2.0")


def _migrate_add_site(data: MutableMapping[str, Any]) -> None:
    """v1→v2：design 补默认空 site（旧项目零扰动——site 全默认即 v2 新建态同构）。"""
    design = data.setdefault("design", {})
    if not isinstance(design, MutableMapping):
        # R 轮 G1-02：非映射 design 禁 AttributeError 裸逃逸——统一经
        # InvalidProjectError（GR-11 族；消息风格对照 io._build 同款中文口径）。
        raise InvalidProjectError(
            f"项目数据 design 须为对象（映射）：得到 {type(design).__name__}"
            "（迁移器 _migrate_add_site 就地变换面——site 键的载体子树）"
        )
    design.setdefault("site", {})


# 链式迁移器注册表（R1）：(源版, 目标版, 迁移器) 按链序排列。
# 迁移器签名：Callable[[MutableMapping[str, Any]], None]——就地纯
# 变换数据树（无 I/O、无随机），每步完成后写入迁移日志结构。
_MIGRATIONS: Final[tuple[tuple[str, str, Callable[[MutableMapping[str, Any]], None]], ...]] = (
    ("1.0", "2.0", _migrate_add_site),
)


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


def _apply_chain(data: Mapping[str, Any], version: str) -> ProjectFile:
    """已知历史版 → 当前版：_MIGRATIONS 链序逐步变换（R1 跳级=链式复合）。

    深拷贝隔离调用方数据树（migrate 对外纯函数——零就地泄漏）；每步
    迁移器就地变换+回写顶层 format_version=目标版；走完同步 metadata
    （format_version=当前版防双写冲突；migrated_from=来源版，多级跳步
    保留最早非空来源——R2 审计面）；链不可达（源版无条目）= 未知
    历史版本拒（既有末段语义同款消息）。
    """
    migrated: MutableMapping[str, Any] = copy.deepcopy(dict(data))
    walked = version
    for source, target, migrator in _MIGRATIONS:
        if source != walked:
            continue  # 非当前步（链序=注册序；源版未入链则全程跳空→末段拒）
        migrator(migrated)
        migrated["format_version"] = target
        walked = target
    current = SUPPORTED_VERSIONS[-1]
    if walked != current:
        raise InvalidProjectError(
            f"未知历史版本：文件 format_version={version!r} 不在合法版本序列"
            f" {list(SUPPORTED_VERSIONS)} 内（R1 链式注册表无该源版路径；"
            "来源不明文件请走 M4 旧系统导入器）"
        )
    metadata = migrated.get("metadata")
    if not isinstance(metadata, MutableMapping):
        metadata = {}
        migrated["metadata"] = metadata
    inner = metadata.get("format_version")
    if inner is not None and inner != version:
        # R 轮 G1-01：链源版与 metadata 声明不一致=真双写冲突——升版写回
        # 前拒（口径同 project_schema._sync_format_version；合法迁移态
        # metadata==源版（app.load_project 路径 model_dump 携带），不拦）。
        raise InvalidProjectError(
            f"format_version 双写冲突：顶层 {version!r} vs metadata {inner!r}"
            "（顶层为权威源——迁移链只读顶层，R5）"
        )
    metadata["format_version"] = current
    if metadata.get("migrated_from") is None:
        metadata["migrated_from"] = version
    return _parse(migrated)


def migrate(data: Mapping[str, Any]) -> ProjectFile:
    """版本识别正门：当前版直通 / 未来版拒 / 历史版经链迁移（R1~R3）。"""
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
    return _apply_chain(data, version)

"""format_version 迁移链：旧版项目 JSON → 当前版对象（链式、可测试）。

输入:  任意历史 format_version 的项目 JSON
输出:  当前版 ProjectFile（迁移路径记录进 metadata.migrated_from）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T7a 实现 D6 裁决 2026-08-25；镜像测试 tests/project/test_migration.py）
#
# 【公开接口】
#   SUPPORTED_VERSIONS: Final[tuple[str, ...]] = ("1.0", "2.0", "3.0", "4.0")
#       迁移链覆盖的版本序列（链尾=当前版，锁定用例 [-1]=="4.0"）；
#       M1 批（site 键）起链启用首条 v1→v2——后续版本只增条目；
#       L4a 批（boundary 红线键，GR-21 只增）追加 v2→v3；inlet-m3d 批
#       2026-10-02（进水参数面 m³/s→m³/d 换轴）追加 v3→v4。
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
#      【L4a 注记】v2→v3 起样本对入链（v2_0_to_3_0_input/expected.json），
#      由 tests/project/test_migration.py 接线（README 纪律兑现）。
#      【inlet-m3d 注记 2026-10-02】v3→v4 样本对入链（v3_0_to_4_0_*.json
#      +舍入口径锚用例）：迁移面=design.nodes 中 kind=="municipal_input"
#      节点的 q_avg_daily ×86400（勘察冻结=恰该形态携带——junction/
#      recycle_junction 零携带、hebing 形单元节点本就 m³/d 面零触碰、
#      design.influent 无消费面零触碰）；换算因子经 contracts.quantity
#      parse 派生（m³/d→m³/s 因子之倒数——R2 禁手写 86400）；舍入定版
#      =round(x,6)（工程口径整洁面 1e-6 m³/d≈1 mL/d+io round-10 幂等
#      前提内稳定——golden 手定 34760.7 为人类录入非迁移产物，注册表
#      存量 0.4023229167 机械迁移=34760.700003，两数 3e-6 m³/d（=3 mL/d
#      ——门一回炉 k2-W2/d1-W3 勘正「≈1 L/d」1000× 失实句）差如实
#      记档批档 impl-report）。
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
#   - 数值纪律：本文件零数值面（inlet-m3d 批 v3→v4 迁移器的 86400 换算
#     经 contracts.quantity parse 派生常量承载——非手写字面量，口径同
#     graph/nodes._SECS_PER_DAY 先例）。
#
# 【测试要求】链式到达、逐步日志、不可迁移拒绝、未来版拒绝、
#   golden 样本往返（v1 后续版本起）。
#
# 【参照】重写计划 §7 M4/§12.3；简报 T7a D6
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import copy
from collections.abc import Callable, Mapping, MutableMapping
from math import isfinite
from typing import Any, Final

from pydantic import ValidationError

from waterprint.contracts.project_schema import ProjectFile, parse_project
from waterprint.contracts.quantity import DimKey, parse
from waterprint.project.io import InvalidProjectError

SUPPORTED_VERSIONS: Final[tuple[str, ...]] = ("1.0", "2.0", "3.0", "4.0")

# 秒/日（=86400，m³/s→m³/d 换算乘子）——经 pint 正门派生（R2 禁手写
# 86400 系数；graph/nodes._SECS_PER_DAY 同源同式——两处非同一份字面量，
# 均为 parse 派生）。inlet-m3d 批 v3→v4 迁移器唯一换算面；命名=语义
# 直陈（门一回炉 k2-N5 2026-10-02 裁「_DAYS_PER_FLOW 晦涩」更名——
# 值=秒数/日，非「日/流量」）。
_SECONDS_PER_DAY: Final[float] = 1.0 / parse(1.0, "m3/d", DimKey.FLOW)
# 迁移舍入定点（round(x, 6) 的位数=6——工程口径整洁面 1e-6 m³/d≈1 mL/d
# 声明常量；门一回炉 k2-W3/d1-N1 2026-10-02 裁「2*2+2 伪装」撤加法式
# 直写真源值——经 check_magic_numbers WHITELIST_DECLARATION 登记本文件
# 声明面放行，cache.py/pipes.py 先例）。
_ROUND_DIGITS_M3D: Final[int] = 6


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


def _migrate_add_boundary(data: MutableMapping[str, Any]) -> None:
    """v2→v3：design.site 补默认空 boundary（L4a 红线键——旧项目零扰动，未划界合法态）。"""
    design = data.setdefault("design", {})
    if not isinstance(design, MutableMapping):
        # _migrate_add_site 同款防御（G1-02 族：非映射容器统一 InvalidProjectError）。
        raise InvalidProjectError(
            f"项目数据 design 须为对象（映射）：得到 {type(design).__name__}"
            "（迁移器 _migrate_add_boundary 就地变换面——boundary 键的载体子树）"
        )
    site = design.setdefault("site", {})
    if not isinstance(site, MutableMapping):
        raise InvalidProjectError(
            f"项目数据 design.site 须为对象（映射）：得到 {type(site).__name__}"
            "（迁移器 _migrate_add_boundary 就地变换面——boundary 键的挂载点）"
        )
    site.setdefault("boundary", [])


def _migrate_inlet_m3d(data: MutableMapping[str, Any]) -> None:
    """v3→v4：进水参数面 m³/s→m³/d 换轴（inlet-m3d 批 2026-10-02）。

    迁移面=design.nodes 中 kind=="municipal_input" 节点的 q_avg_daily
    ×86400（勘察冻结恰该形态携带；hebing 形单元节点 q_avg_daily 本就
    m³/d 面零触碰）。换算经 _SECONDS_PER_DAY（pint 派生）；舍入=round(,6)
    定版（测试锚 test_v3_to_v4_rounding_policy_anchored）。乘换算后两闸
    fail-loud（门一回炉 d1-W2 2026-10-02——主控实证 NaN 静默穿透）：①
    换算积非有限（NaN/±inf，含有限原值乘换算溢出）拒；②迁移积 round 后
    ≤0.0 拒——拒因分模板（门一回炉轮 2 k2-W1 2026-10-02）：原值非正
    （0/负——非法进水流量）与正值过小 round6 归零两族分流，套同一句
    「值过小」对 0/负名不副实。非映射容器统一
    InvalidProjectError（G1-02 族防御同前两条迁移器）。
    """
    design = data.setdefault("design", {})
    if not isinstance(design, MutableMapping):
        raise InvalidProjectError(
            f"项目数据 design 须为对象（映射）：得到 {type(design).__name__}"
            "（迁移器 _migrate_inlet_m3d 就地变换面——进水换轴的载体子树）"
        )
    nodes = design.setdefault("nodes", {})
    if not isinstance(nodes, MutableMapping):
        raise InvalidProjectError(
            f"项目数据 design.nodes 须为对象（映射）：得到 {type(nodes).__name__}"
            "（迁移器 _migrate_inlet_m3d 就地变换面——municipal_input 节点表）"
        )
    for node_id, node in nodes.items():
        if not isinstance(node, MutableMapping) or node.get("kind") != "municipal_input":
            continue  # 迁移面=恰 municipal_input kind（勘察冻结——余节点零触碰）
        if "q_avg_daily" not in node:
            continue  # 键缺席=空参节点合法中间态（GR-09 键存在性校验在装配期）
        value = node["q_avg_daily"]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise InvalidProjectError(
                f"design.nodes[{node_id!r}].q_avg_daily 须为数值：得到 {value!r}"
                "（v3→v4 进水换轴不可猜测性迁移——R2 禁猜测性默认，G1-02 族）"
            )
        product = float(value) * _SECONDS_PER_DAY
        if not isfinite(product):
            raise InvalidProjectError(
                f"design.nodes[{node_id!r}].q_avg_daily 换算积非有限值："
                f"原值 {value!r}（v3 m³/s）×86400 → {product!r}"
                "（v3→v4 进水换轴 fail-loud——NaN/±inf 禁静默穿透入 v4 面，"
                "R2 禁猜测性默认；门一回炉 d1-W2 2026-10-02）"
            )
        migrated_value = round(product, _ROUND_DIGITS_M3D)
        if migrated_value <= 0.0:
            # 拒因分模板（门一回炉轮 2 k2-W1 2026-10-02）：原值非正
            # （0/负——非法进水流量）与正值过小 round6 归零两族分流
            # ——0/负套「值过小」名不副实（0 非「小」是非法）。
            reason = (
                "v3 值非正（0/负——非法进水流量）" if value <= 0 else "v3 值过小"
            )
            raise InvalidProjectError(
                f"design.nodes[{node_id!r}].q_avg_daily {reason}：原值 {value!r}"
                f"（v3 m³/s），迁移积 {product!r} m³/d，round {_ROUND_DIGITS_M3D}"
                f" 位后 {migrated_value!r}（≤0 不可承载 v4 m³/d 正值面"
                "——fail-loud 拒猜测性默认；门一回炉 d1-W2 2026-10-02）"
            )
        node["q_avg_daily"] = migrated_value


# 链式迁移器注册表（R1）：(源版, 目标版, 迁移器) 按链序排列。
# 迁移器签名：Callable[[MutableMapping[str, Any]], None]——就地纯
# 变换数据树（无 I/O、无随机），每步完成后写入迁移日志结构。
_MIGRATIONS: Final[tuple[tuple[str, str, Callable[[MutableMapping[str, Any]], None]], ...]] = (
    ("1.0", "2.0", _migrate_add_site),
    ("2.0", "3.0", _migrate_add_boundary),
    ("3.0", "4.0", _migrate_inlet_m3d),
)


def _version_key(version: str) -> tuple[int, ...] | None:
    """点分数值版本串 → 整数序元组（"1.0"→(1,0)）；非数值格式 → None。

    REWORK 审查 G1-01（2026-09-09）：isdigit 判定域逃逸收口——"②"/"²"
    等 Unicode 数字 isdigit 真而 int() 裸 ValueError（与 PROFILE3 批
    `_scale_denom_of` 同型）；isdecimal 前置 + int() 收编 try/except
    （超长段 ≥3.11 的 4300 位上限同族）→ crafted 版本串一律归 None
    =「未知历史版本」拒绝族（InvalidProjectError 4xx 语义，禁裸逃逸）。
    G1-02：str.split(".") 恒非空列表，原 `not parts` 守卫为死分支，撤。
    """
    parts = version.split(".")
    if not all(part.isdecimal() for part in parts):
        return None
    try:
        return tuple(int(part) for part in parts)
    except ValueError:
        return None


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

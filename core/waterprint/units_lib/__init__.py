"""L2 工艺单元库包根：四条业务线物理隔离，单元发现机制唯一入口。

输入:  各单元包的 manifest + compute（经包 __init__ 白名单导出）
输出:  单元注册表构建 API（供 L4 app.py 装配；图引擎不认识这里）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；T7b D6 最小实现 2026-08-25）
#
# 【导出白名单】
#   discover_units() -> Mapping[unit_id → (UnitManifest, Unit 工厂)]
#       扫描四条线各包的 __init__ 白名单导出（不 exec 任意代码；
#       发现失败/重复 unit_id = 启动失败）
#
# 【T7b D6 最小实现注记】（2026-08-25）
#   - 骨架包无导出 = 跳过不报错——**空注册表合法**（M1 各单元实装后
#     自然填充；T7b 测试链零依赖本函数产物：三内置节点不经 units_lib）。
#   - 白名单导出面 = manifest + make_unit 两名（AGENTS §11"只暴露
#     manifest 与 compute"的工厂形态读法——compute 是 make_unit 的
#     内部依赖；UF-29 拍板前以工厂面落，M1 复核）。
#   - 导出非法定义（仅单名/他名）或重复 unit_id = 启动失败：
#     最小 raise RuntimeError 带 GR-09 上下文（units_lib 侧异常族未定，
#     M1 定族；空实现下不可达，防御性）。
#
# 【铁律】
#   - 单元之间互相独立（import-linter independence 契约）；
#   - "同名构筑物"跨线各自成包（市政高密池 vs 矿井水高密池），
#     禁止参数复用造成的暗耦合（§14.3）；
#   - 单元只依赖 L0+L1，禁止 import L3（分层契约）；
#   - 新单元 = `wp new-unit <line> <name>`（cli.py）从 _template 生成；
#   - 单元间业务规则（参数初始化链/耦合归属/守恒点/可行解流程/
#     回路标记）统一见 docs/business-logic.md，包内规格与之对齐。
#
# 【单元归属（ADR-007 附表摘要，32 包；M0.5 起已全部落地为骨架，
#   业务身份总表见 docs/structure-graph.md §3，三方互验由
#   scripts/check_module_graph.py 强制）】
#   municipal（13）：粗格栅/细格栅/旋流沉砂池/辐流初沉池/调节池/AAO/
#     CASS/高密沉淀池/V型滤池/紫外消毒 + 辐流二沉池/巴歇尔计量槽/
#     污水提升泵房                                  → M2
#   mine_water（8）：矿井水输入/调节池/平流沉砂池/混凝反应/磁分离/
#     高密沉淀/V型滤池/紫外消毒                     → M3
#   sludge（7）：合并/输送/泵站/浓缩/消化/脱水/干化 → M3
#   conveyance（4）：集水井/配水井/集配水井/配水渠 → M3
#   折叠为配置（非单元）：旧 jcws_smbg、gdys_stss → elevation 输入
#   内置图节点（非单元包）：市政输入/汇流/水质编辑 → graph 内置类型
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import Final

from waterprint.contracts.manifest import UnitManifest
from waterprint.contracts.unit_api import Unit

_LINES: Final[tuple[str, ...]] = ("municipal", "mine_water", "sludge", "conveyance")
# 白名单导出面（manifest + make_unit 两名——见【T7b D6 最小实现注记】）。
_UNIT_EXPORTS: Final[frozenset[str]] = frozenset({"manifest", "make_unit"})


def _register(
    registry: dict[str, tuple[UnitManifest, Callable[[], Unit]]],
    module_name: str,
    exports: frozenset[str],
    manifest: object,
    factory: object,
) -> None:
    """单包登记守卫：非法定义/类型不符/重复 unit_id = 启动失败（GR-09 上下文）。"""
    if exports != _UNIT_EXPORTS:
        raise RuntimeError(
            f"单元包 {module_name} 导出非法定义：{sorted(exports)}"
            f"（白名单 {sorted(_UNIT_EXPORTS)}——AGENTS §11 两名铁律；"
            "部分导出=装配缺陷）"
        )
    if not isinstance(manifest, UnitManifest):
        raise RuntimeError(
            f"单元包 {module_name} 的 manifest 非 UnitManifest："
            f"得到 {type(manifest).__name__}（经 load_manifest 构造后登记）"
        )
    if not callable(factory):
        raise RuntimeError(
            f"单元包 {module_name} 的 make_unit 不可调用：{factory!r}"
        )
    if manifest.unit_id in registry:
        raise RuntimeError(
            f"重复 unit_id：{manifest.unit_id!r}（{module_name} 与既有条目"
            "冲突——units_lib 铁律：注册表键唯一）"
        )
    registry[manifest.unit_id] = (manifest, factory)


def discover_units() -> Mapping[str, tuple[UnitManifest, Callable[[], Unit]]]:
    """扫描四线各包 __init__ 白名单导出 → 单元注册表（骨架无导出=空表合法）。"""
    registry: dict[str, tuple[UnitManifest, Callable[[], Unit]]] = {}
    for line in _LINES:
        package = importlib.import_module(f"waterprint.units_lib.{line}")
        for module_info in pkgutil.iter_modules(package.__path__):
            module = importlib.import_module(
                f"waterprint.units_lib.{line}.{module_info.name}"
            )
            exports = frozenset(
                name for name in _UNIT_EXPORTS if hasattr(module, name)
            )
            if not exports:
                continue  # 骨架包无导出=跳过（空注册表合法——D6 裁决）
            _register(
                registry,
                module.__name__,
                exports,
                getattr(module, "manifest", None),
                getattr(module, "make_unit", None),
            )
    return MappingProxyType(registry)

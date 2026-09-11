"""出水标准装载器（constraint_kb effluent_standard 条目 → EffluentStandard 族）。

输入:  data/constraint_kb/constraints.json（kind=effluent_standard 12 条——
       GB 18918-2002 一级A/B×六项，Ruling 2026-08-31 已追认参考面）
输出:  load_effluent_standards(path) -> tuple[EffluentStandard, ...]
       （quality.EffluentStandard——UF-39 装载面落地：quality.py 零 I/O
       纪律保持，STANDARDS 符号不进 contracts；本件=server 装配调用）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（P2 次批 ADR-012 D6；镜像测试 tests/registry/test_effluent.py）
#
# 【公开接口】
#   load_effluent_standards(path: str | Path) -> tuple[EffluentStandard, ...]
#       按 standard_id 字典序返回（GR-18 确定性）
#   class InvalidEffluentLoadError(Exception)（GR-11 族，本文件定义）
#
# 【行为规格】
#   R1 条目筛 kind=effluent_standard；key 三段式 {standard}.{grade}.{ind}
#       （standard_id=key 去尾段）；expression 受限形态
#       "{INDICATOR}_out <= {limit}"——指标从 expression 前缀提取
#       （CODCR 大写直取——key 尾段 bod5/cod 与 INDICATORS 存在拼写差，
#       禁经 key 映射）；限值经 float 后有限且 >0（quality.margin 域前置）。
#   R2 同 standard_id 组内 label 标准名段（" 出水 " 前段）必须一致——
#       数据固定资产格式契约（不一致=数据缺陷拒，fail-fast R3 同源）。
#   R3 fail-fast（quality.R3 同精神）：文件缺失/JSON 非法/条目零条/
#       expression 非法/指标未知/限值域拒/名称段不一致——一律
#       InvalidEffluentLoadError（消息含条目 key 与期望形态），禁止
#       回退默认标准、禁止静默跳条。
#   R4 指标集合开放（quality.R4 同款）：不强制每标准恰六项——条目
#       有则装载（域守卫集中在条目级）；重复 (standard_id, indicator)
#       拒。
#
# 【数值纪律】本文件不在魔法数字白名单——数值字面量仅 0（限值 >0 域）。
#
# 【测试要求】真源数据装载（2 标准×6 指标全量断言）/缺文件拒/非法
#   expression 拒/未知指标拒/限值域拒/名称段不一致拒/重复条目拒/
#   字典序确定性。
#
# 【参照】ADR-012；quality.py（EffluentStandard/margin/INDICATORS）；
# registry/coefficients.py（L1 装载器纪律母本）；UF-39
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import re
from math import isfinite
from pathlib import Path
from typing import Final, final

from waterprint.contracts.quality import INDICATORS, EffluentStandard

# expression 受限形态：{INDICATOR}_out <= {limit}（空白弹性；指标大写集内）
_EXPRESSION: Final[re.Pattern[str]] = re.compile(
    r"^([A-Z][A-Z0-9]*)_out\s*<=\s*([0-9][0-9.eE+-]*)$"
)
_NAME_SPLIT: Final[str] = " 出水 "
# key 三段式段数（{standard}.{grade}.{ind}——PLR2004 常量化）
_KEY_SEGMENTS: Final[int] = 3


class InvalidEffluentLoadError(Exception):
    """出水标准装载非法（文件/条目形态/域）——领域异常（GR-11 族）。"""


@final
class _Entry:
    """中间条目：standard_id + 指标 + 限值 + 标准名段（label 派生）。"""

    __slots__ = ("indicator", "limit", "name", "standard_id")

    def __init__(self, standard_id: str, indicator: str, limit: float, name: str) -> None:
        self.standard_id = standard_id
        self.indicator = indicator
        self.limit = limit
        self.name = name


def _entry_of(raw: object, where: str) -> _Entry:
    """单条目解析：key 三段式+expression 受限形态+label 名段（R1/R2）。"""
    if not isinstance(raw, dict):
        raise InvalidEffluentLoadError(
            f"{where} 须为对象（constraint_kb 条目形态）：得到 {type(raw).__name__}"
        )
    key = raw.get("key")
    if not isinstance(key, str) or len(key.split(".")) != _KEY_SEGMENTS:
        raise InvalidEffluentLoadError(
            f"{where} 的 key 须为三段式 {{standard}}.{{grade}}.{{ind}}：{key!r}"
        )
    standard_id = key.rsplit(".", 1)[0]
    expression = raw.get("expression")
    if not isinstance(expression, str):
        raise InvalidEffluentLoadError(
            f"{where}（{key!r}）的 expression 须为字符串：{expression!r}"
        )
    matched = _EXPRESSION.match(expression)
    if matched is None:
        raise InvalidEffluentLoadError(
            f"{where}（{key!r}）的 expression 须为受限形态 "
            f"{{INDICATOR}}_out <= {{limit}}：{expression!r}"
        )
    indicator, limit_text = matched.group(1), matched.group(2)
    if indicator not in INDICATORS:
        raise InvalidEffluentLoadError(
            f"{where}（{key!r}）的指标 {indicator!r} 不在 INDICATORS "
            f"{sorted(INDICATORS)}（quality.R4 扩展走 dimensions 注册）"
        )
    limit = float(limit_text)
    if not isfinite(limit) or limit <= 0:
        raise InvalidEffluentLoadError(
            f"{where}（{key!r}）的限值必须为有限且 > 0：{limit_text!r}"
            "（quality.margin 域前置——装载面拒带病限值）"
        )
    label = raw.get("label")
    if not isinstance(label, str) or _NAME_SPLIT not in label:
        raise InvalidEffluentLoadError(
            f"{where}（{key!r}）的 label 须含标准名段（{_NAME_SPLIT!r} 分隔）：{label!r}"
        )
    return _Entry(standard_id, indicator, limit, label.split(_NAME_SPLIT)[0])


def load_effluent_standards(path: str | Path) -> tuple[EffluentStandard, ...]:
    """装载正门：constraints.json effluent_standard 条目 → 标准族（字典序）。

    UF-39 装载面落地（ADR-012 D6）：quality.py 保持零 I/O——本件为
    唯一装载通道（server worker 数据装配调用；core 测试注入 fixture 同门）。
    """
    file = Path(path)
    if not file.is_file():
        raise InvalidEffluentLoadError(
            f"出水标准数据文件缺失：{file!r}（constraint_kb 固定资产——"
            "缺文件=数据装配缺陷，fail-fast 拒默认回退 R3）"
        )
    try:
        tree = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidEffluentLoadError(
            f"出水标准数据文件不可读/非法 JSON：{file!r}（{exc}）"
        ) from exc
    entries = tree.get("entries") if isinstance(tree, dict) else None
    if not isinstance(entries, list):
        raise InvalidEffluentLoadError(
            f"{file.name} 须为含 entries 数组的对象（constraint_kb 形态）"
        )
    for index, raw in enumerate(entries):
        # R3 fail-fast：非对象条目=数据缺陷拒（禁静默跳条）；对象但
        # kind 非 effluent_standard=正常过滤（约束库多 kind 并存）。
        if not isinstance(raw, dict):
            raise InvalidEffluentLoadError(
                f"{file.name} entries[{index}] 须为对象（constraint_kb 条目"
                f"形态）：得到 {type(raw).__name__}"
            )
    parsed = [
        _entry_of(raw, f"{file.name} entries[{index}]")
        for index, raw in enumerate(entries)
        if raw.get("kind") == "effluent_standard"
    ]
    if not parsed:
        raise InvalidEffluentLoadError(
            f"{file.name} 无 kind=effluent_standard 条目（12 条固定资产——"
            "零条即数据缺陷，R3 fail-fast）"
        )
    grouped: dict[str, dict[str, float]] = {}
    names: dict[str, str] = {}
    for entry in parsed:
        seen = grouped.setdefault(entry.standard_id, {})
        if entry.indicator in seen:
            raise InvalidEffluentLoadError(
                f"标准 {entry.standard_id!r} 指标 {entry.indicator!r} 重复"
                "（constraint_kb 条目冲突——R4 重复拒）"
            )
        seen[entry.indicator] = entry.limit
        known = names.setdefault(entry.standard_id, entry.name)
        if known != entry.name:
            raise InvalidEffluentLoadError(
                f"标准 {entry.standard_id!r} 组内标准名段不一致："
                f"{known!r} vs {entry.name!r}（R2 数据格式契约）"
            )
    return tuple(
        EffluentStandard(
            standard_id=standard_id, name_i18n=names[standard_id], limits=limits
        )
        for standard_id in sorted(grouped)
        for limits in (dict(grouped[standard_id]),)
    )

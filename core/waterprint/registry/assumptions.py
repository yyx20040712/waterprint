"""设计假设清单唯一真源：数值面 YAML 外置（B2-4），本件=守卫面+装载器+取值正门。

输入:  data/assumptions/ 数据包（manifest 有序清单+四件条目）+伴生件类注入
输出:  AssumptionSet（注入 UnitContext；项目可保存覆盖值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（批次: b2-s1-assumptions-yaml；镜像测试 tests/registry/test_assumptions.py；
# 守卫语义/公开签名/R1~R4=改造前 500 行版（git 史）；口径/哨兵/版本=定案 §4.3/§4.6/§4.7；
# 消息与 docstring 预算精简；四注册表互不 import、禁写 data/**；伴生注入尾挂（防环）。
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Final, final

import yaml

from waterprint.contracts.quantity import DimKey
from waterprint.registry.assumptions_design_map import design_map_entries

_YAML_DATA_DIR: Final[Path] = Path(__file__).resolve().parents[2].parent / "data" / "assumptions"
_MANIFEST_KEYS: Final[frozenset[str]] = frozenset({"ordered_files", "schema_version"})
_ENTRY_KEYS: Final[frozenset[str]] = frozenset(
    ["key", "default", "dim", "source", "note", "tuning_impact"]
)
_TUNING_KEYS: Final[frozenset[str]] = frozenset({"direction", "constraint_keys"})
_SCHEMA_VERSION: Final[int] = 1


class InvalidAssumptionError(Exception):
    ...


def _nonempty_str(value: object, what: str) -> str:
    if not isinstance(value, str) or not value:
        raise InvalidAssumptionError(f"{what} 必须为非空字符串：得到 {value!r}")
    return value


def _number(value: object, key: str, what: str, *, no_str: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, str | int | float):
        raise InvalidAssumptionError(f"假设 {key!r} 的 {what} 须为数值（bool 拒）：{value!r}")
    if no_str and isinstance(value, str):
        raise InvalidAssumptionError(f"假设 {key!r} 的 {what} 不收字符串：{value!r}")
    try:
        number = float(value)
    except (ValueError, OverflowError) as exc:
        raise InvalidAssumptionError(f"假设 {key!r} 的 {what} 非法或超浮点域：{value!r}") from exc
    if not isfinite(number):
        raise InvalidAssumptionError(f"假设 {key!r} 的 {what} 非有限：{number!r}")
    assert type(number) is float  # W10 终检
    return number


def _normalize_dim(value: DimKey | str, key: str) -> DimKey:
    if isinstance(value, DimKey):
        return value
    if not isinstance(value, str):
        raise InvalidAssumptionError(f"假设 {key!r} 的 dim 须为 DimKey 或成员名：{value!r}")
    try:
        return DimKey(value)
    except ValueError as exc:
        raise InvalidAssumptionError(
            f"假设 {key!r} dim 非法：{value!r}（合法 {sorted(m.value for m in DimKey)}）"
        ) from exc


@dataclass(frozen=True)
@final
class TuningImpact:
    direction: str
    constraint_keys: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.constraint_keys, Sequence) or isinstance(
            self.constraint_keys, str | bytes | Mapping
        ):
            raise InvalidAssumptionError(f"constraint_keys 须为键序列：{self.constraint_keys!r}")
        _nonempty_str(self.direction, "TuningImpact.direction（调节方向短语）")
        normalized = tuple(self.constraint_keys)
        if not all(isinstance(element, str) and element for element in normalized):
            raise InvalidAssumptionError(f"constraint_keys 元素须为非空 str：{normalized!r}")
        object.__setattr__(self, "constraint_keys", normalized)


@dataclass(frozen=True)
@final
class Assumption:
    key: str
    default: float
    dim: DimKey | str
    source: str
    note: str
    tuning_impact: TuningImpact | None = None

    def __post_init__(self) -> None:
        key = _nonempty_str(self.key, "假设 key")
        if self.tuning_impact is None:
            raise InvalidAssumptionError(f"假设 {key!r} 缺 tuning_impact（R2 缺一不可）")
        object.__setattr__(self, "key", key)
        object.__setattr__(self, "default", _number(self.default, key, "default"))
        object.__setattr__(self, "dim", _normalize_dim(self.dim, key))
        object.__setattr__(self, "source", _nonempty_str(self.source, f"假设 {key!r} 的 source"))
        object.__setattr__(self, "note", _nonempty_str(self.note, f"假设 {key!r} 的 note"))


@dataclass(frozen=True)
@final
class AssumptionSet:
    _items: tuple[Assumption, ...]

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for item in self._items:
            if item.key in seen:
                raise InvalidAssumptionError(f"假设键重复：{item.key!r}（重复=装配缺陷）")
            seen.add(item.key)
        object.__setattr__(self, "_items", tuple(self._items))

    def __iter__(self) -> Iterator[Assumption]: return iter(self._items)

    def __getitem__(self, index: int) -> Assumption: return self._items[index]

    def __len__(self) -> int: return len(self._items)

    def keys(self) -> tuple[str, ...]: return tuple(sorted(item.key for item in self._items))


def assumption(key: str, overrides: Mapping[str, float]) -> float:
    """取值正门（R1 根治点）：覆盖值优先，否则默认值；未知键=领域异常。"""
    if not isinstance(overrides, Mapping):
        raise TypeError(f"overrides 须为 Mapping：{type(overrides).__name__}（GR-08）")
    for item in DEFAULT_ASSUMPTIONS:
        if item.key == key:
            if key in overrides:
                return _number(overrides[key], key, "覆盖值", no_str=True)
            return item.default
    raise InvalidAssumptionError(f"未登记假设：{key!r}（禁止静默默认）")


def _load_yaml(path: Path, what: str) -> object:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, UnicodeDecodeError, OSError) as exc:
        raise InvalidAssumptionError(f"{what} {path.name} 装载失败：{exc}") from exc


def _load_manifest() -> list[str]:
    path = _YAML_DATA_DIR / "manifest.yaml"
    if not path.is_file():
        raise InvalidAssumptionError(f"假设包缺 manifest.yaml：{path}（装载序载体）")
    data = _load_yaml(path, "清单文件")
    if not isinstance(data, dict):
        raise InvalidAssumptionError(f"manifest.yaml 顶层须为映射：{type(data).__name__}")
    if extra := sorted(set(data) - _MANIFEST_KEYS):
        raise InvalidAssumptionError(f"manifest.yaml 未知键：{extra}")
    ordered = data.get("ordered_files")
    if not isinstance(ordered, list) or not ordered or not all(
        isinstance(name, str) and name for name in ordered
    ):
        raise InvalidAssumptionError("ordered_files 须为非空字符串列表=装载序（GR-14）")
    version = data.get("schema_version")
    if isinstance(version, bool) or not isinstance(version, int) or version != _SCHEMA_VERSION:
        raise InvalidAssumptionError(f"schema_version 须为 int={_SCHEMA_VERSION}：{version!r}")
    return list(ordered)


def _parse_entry(where: str, raw: object) -> Assumption:
    if not isinstance(raw, dict):
        raise InvalidAssumptionError(f"条目形态非法（{where}）：须为六键映射")
    if set(raw) != _ENTRY_KEYS:
        raise InvalidAssumptionError(f"条目键集非法（{where}）：{sorted(set(raw) ^ _ENTRY_KEYS)}")
    tuning = raw["tuning_impact"]
    if not isinstance(tuning, dict) or set(tuning) != _TUNING_KEYS:
        raise InvalidAssumptionError(f"tuning_impact 须为恰两键（{where}）：{sorted(_TUNING_KEYS)}")
    key = _nonempty_str(raw["key"], f"条目 key（{where}）")
    return Assumption(
        key, _number(raw["default"], key, "default"), raw["dim"], raw["source"], raw["note"],
        TuningImpact(tuning["direction"], tuning["constraint_keys"]),
    )


def _load_items() -> tuple[Assumption, ...]:
    items: list[Assumption] = []
    for name in _load_manifest():
        data = _load_yaml(_YAML_DATA_DIR / name, "条目文件")
        if not isinstance(data, list) or not data:
            raise InvalidAssumptionError(f"条目文件 {name} 顶层须为非空列表（GR-14）")
        items.extend(_parse_entry(f"{name}[{index}]", raw) for index, raw in enumerate(data))
    return tuple(items)


DEFAULT_ASSUMPTIONS: Final[AssumptionSet] = AssumptionSet(
    _items=(*_load_items(), *design_map_entries(Assumption, TuningImpact))
)

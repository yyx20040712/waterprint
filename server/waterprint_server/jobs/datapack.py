"""数据包适配域件：系数包 YAML 镜像装载（CoefficientsView 协议适配器）。

输入:  数据包目录（manifest.yaml 版本头 + 条目 *.yaml 列表文件）
输出:  DataPackError/_CoefficientEntry/_YamlCoefficients（worker 顶部 import
       同名再导出——消费面零改动）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B3 R5 拆分 2026-09-05：DataPackError/_CoefficientEntry/
#   _YamlCoefficients 三符号自 worker.py 数据包适配域随域整迁——
#   yaml/isfinite/Path/Mapping 四依赖零 worker 依赖自足（worker 500 行
#   预算减压）；搬运零行为变化（docstring/报文逐字随迁），worker 顶部
#   import 同名再导出（DS 必改采纳——_build_env 消费 _YamlCoefficients，
#   DataPackError 消费面 from worker import 不变）
#
# 【行为规格】
#   R-1 装载语义与 registry.load_coefficients 同款（B4 双胞胎）：manifest
#      .yaml 版本头 + 其余 *.yaml 按名排序；键全包唯一；数值有限性 GR-02；
#      空条目包 GR-14 拒（报文随迁零变）。
#   R-2 导入零副作用（Windows spawn 铁律——本模块只做类定义零全局态）。
#
# 【测试要求】经 worker 再导出面由既有镜像测试覆盖（tests/jobs/
#   test_worker.py 装载矩阵用例零波移）。
#
# 【参照】B3 简报 R5；重写计划 §13.4/§18
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Mapping
from math import isfinite
from pathlib import Path

import yaml


class DataPackError(ValueError):
    """数据包装载非法（manifest/条目形态）——领域异常（GR-11 族）。"""


class _CoefficientEntry:
    """系数条目视图（CoefficientsView.get 的返回协议面：value/unit/source/note）。"""

    def __init__(self, value: float, unit: str, source: str, note: str) -> None:
        self.value = value
        self.unit = unit
        self.source = source
        self.note = note


class _YamlCoefficients:
    """CoefficientsView 协议适配器：registry 数据包格式镜像装载（B4 双胞胎）。

    只实现 L0 协议查询面（data_version/get/keys/require_keys）——装载
    语义与 registry.load_coefficients 同款（manifest.yaml 版本头 + 其余
    *.yaml 条目按名排序；键全包唯一；数值有限性 GR-02）。
    """

    def __init__(self, directory: Path) -> None:
        manifest = directory / "manifest.yaml"
        if not manifest.is_file():
            raise DataPackError(f"系数包缺 manifest.yaml：{directory}（装载面只认数据包目录）")
        manifest_data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
        if not isinstance(manifest_data, Mapping) or not isinstance(
            manifest_data.get("data_version"), str
        ):
            raise DataPackError(f"系数包 manifest.yaml 形态非法（缺 data_version）：{manifest}")
        self.data_version = manifest_data["data_version"]
        self._entries: dict[str, _CoefficientEntry] = {}
        for entry_file in sorted(directory.glob("*.yaml")):
            if entry_file.name == "manifest.yaml":
                continue
            raw = yaml.safe_load(entry_file.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                raise DataPackError(f"条目文件须为列表：{entry_file}")
            for item in raw:
                if not isinstance(item, Mapping):
                    raise DataPackError(f"条目须为对象：{entry_file} 内 {item!r}")
                key = item.get("key")
                value = item.get("value")
                if not isinstance(key, str) or not key or not isinstance(value, (int, float)):
                    raise DataPackError(f"条目缺 key/value 基本字段：{entry_file} 内 {item!r}")
                if isinstance(value, float) and not isfinite(value):
                    raise DataPackError(f"条目数值非有限（GR-02）：{key}={value!r}")
                if key in self._entries:
                    raise DataPackError(f"系数键重复（键全包唯一）：{key}（{entry_file.name}）")
                self._entries[key] = _CoefficientEntry(
                    float(value),
                    str(item.get("unit", "")),
                    str(item.get("source", "")),
                    str(item.get("note", "")),
                )
        if not self._entries:
            raise DataPackError(f"系数包无条目文件（GR-14 空集显式拒）：{directory}")

    def get(self, key: str) -> _CoefficientEntry:
        """键查询（缺键=KeyError——与 registry.Coefficients 同语义）。"""
        return self._entries[key]

    def keys(self, prefix: str = "") -> tuple[str, ...]:
        """前缀键枚举（排序确定性）。"""
        return tuple(sorted(key for key in self._entries if key.startswith(prefix)))

    def require_keys(self, keys: object) -> None:
        """在册断言（协议面）。"""
        if isinstance(keys, (list, tuple)):
            for key in keys:
                if key not in self._entries:
                    raise DataPackError(f"系数键在册断言失败：{key!r}")

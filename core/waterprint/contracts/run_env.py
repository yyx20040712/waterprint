"""执行环境上下文契约：RunEnv——装配一次、执行期只读（UF-31 下沉 L0）。

输入:  引擎版本 + 数据包聚合版本（系数/单价）+ 假设/系数/单价 + 迹收集器
输出:  RunEnv（不可变）——执行期参与可复算三元组的一切只读上下文；
       CoefficientsView/CoefficientValueView 协议与 EngineParam（本文件
       定义，L0 不 import L1——依赖倒置先例 manifest._DimensionSpec）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T7a 实现 D1 裁决 2026-08-25；镜像测试 tests/contracts/test_run_env.py）
#
# 【公开接口】
#   @dataclass(frozen=True) class RunEnv 恰七字段（锁定集，多一少一=
#       规格漂移——锁定用例 dataclasses.fields 全集断言）：
#       engine_version: str（引擎版本，非空）
#       data_version: str（系数+单价聚合——ARCH1 D4 定稿：包集=
#           {coefficients, unit_prices} 两包、name=目录实名，UF-10 T4
#           冻结：包名排序后 name@version 以 + 拼接；app 装配层生成）
#       assumptions: Mapping[str, float]（假设覆盖快照）
#       coefficients: CoefficientsView（协议只读面，registry.
#           Coefficients 结构满足）
#       price_book: Mapping[str, Any]（M3 单价包装载后收紧——GR-21）
#       trace_sink: TraceSink | None（contracts/trace_api 协议）
#       engine_params: Mapping[str, EngineParam]（引擎技术参数，
#           UF-08：app 装配 T7b 从 assumptions 提取 loop.* 三键投影
#           EngineParam 构造——数值真源在 registry/assumptions）
#   class CoefficientsView(Protocol)：data_version: str 只读属性 +
#       get(key)/keys(prefix="")/require_keys(keys) 方法面
#   class CoefficientValueView(Protocol)：value: float / unit: str /
#       source: str / note: str 只读面
#   @dataclass(frozen=True) class EngineParam：value: float /
#       source: str / note: str（GR-15 出处门槛同向：source/note
#       非空、value 非 bool 且有限 GR-02）
#   class InvalidRunEnvError(Exception)（GR-11 Invalid* 族）
#
# 【行为规格】
#   R1 类型家：RunEnv 定义于本契约（L0）——graph/executor.py(L3) 与
#      solution/enumerate.py(L3) 公开签名 `env: RunEnv` 只 import 本
#      文件，不上溯 app.py(L4)（UF-31 分层矛盾消解）；app.py 装配并
#      重新导出（SENS-B 2026-08-23 UF-31）。
#   R2 引擎技术参数（loop 阻尼/容差/缓存上限，UF-08 项）以"带调节
#      影响元数据的引擎默认"条目入 engine_params 字段——数值真源为
#      registry/assumptions 的 loop.* 条目（T7a D2 冻结：tolerance=
#      1e-10 / max_iterations=200 / damping=0.8），app 装配（T7b）
#      提取 loop.* 三键投影 EngineParam 构造 engine_params——本
#      文件只落类型与投影口径，禁散落代码字面量（GR-15 同向）。
#   R3 不可变：装配一次、执行期只读；执行期改写 = FrozenInstanceError
#      （frozen 数据类自然防护；程序缺陷不包装——GR-08，与
#      test_run_env.py 镜像断言一致；SENS-R1 SA-02 口径统一）。
#      assumptions/price_book/engine_params 三个 Mapping 字段构造即
#      快照 MappingProxyType（T3A-01 防线：外部改原容器不泄漏；
#      eq 对同内容代理成立——锁定确定性用例依赖。【T7a 注记】简报
#      D1 原文"四 Mapping"系计数勘误：七字段中 Mapping 类型恰三个，
#      coefficients 是 CoefficientsView 协议对象（registry.
#      Coefficients 的 get 是领域异常语义非 Mapping.get，不可盲
#      dict() 快照），透传不复制——真 Coefficients 实例自身已
#      frozen + 内部快照）。
#   R4 trace_sink 遵循 contracts/trace_api.py 协议（registry 与迹
#      收集器的唯一耦合面），本契约只携带不实现。
#   R5 本文件是 L0 契约（GR-36 类②跨层协议：L3 executor/enumerate
#      与 L4 app 共用），禁 I/O、禁运行时可变状态、禁 import L1
#      registry——系数库只经 CoefficientsView 协议耦合（依赖倒置
#      先例 manifest._DimensionSpec；trace_api 同层 import 合法）。
#
# 【测试要求】不可变性（改写抛 FrozenInstanceError，GR-08 程序缺陷
#   不包装——SENS-R1 SA-02 对齐）、字段完备（七字段全集）、同输入
#   两次构造逐字段相等（确定性）；EngineParam 出处门槛与协议结构
#   满足面由探针举证（真 Coefficients 实例代入）。
#
# 【参照】重写计划 §13.1 装配点；UF-31/UF-08/UF-10（register）；
#   GR-36/GR-15/GR-02（conventions）；简报 T7a D1
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Any, Protocol, final

from waterprint.contracts.trace_api import TraceSink


class InvalidRunEnvError(Exception):
    """RunEnv/EngineParam 构造非法（守卫拒绝）——领域异常（GR-11 Invalid* 族）。"""


def _nonempty_str(value: object, what: str) -> str:
    """非空 str 守卫：类型不符/空串均拒，消息含字段名+原值（GR-15 出处门槛）。"""
    if not isinstance(value, str) or not value:
        raise InvalidRunEnvError(f"{what} 必须为非空字符串：得到 {value!r}")
    return value


class CoefficientValueView(Protocol):
    """系数值只读面：registry.CoefficientValue 的结构满足本协议（R5 倒置）。"""

    @property
    def value(self) -> float: ...

    @property
    def unit(self) -> str: ...

    @property
    def source(self) -> str: ...

    @property
    def note(self) -> str: ...


class CoefficientsView(Protocol):
    """系数库只读面：registry.Coefficients 的结构满足本协议（R5 倒置）。

    L0 契约不 import L1 registry——执行环境只依赖此查询面；
    data_version 是可复算三元组成员（§16 A8）。
    """

    @property
    def data_version(self) -> str: ...

    def get(self, key: str) -> CoefficientValueView:
        """查询正门：未知键由实现方以领域异常拒（禁 None 假装成功）。"""
        ...

    def keys(self, prefix: str = "") -> tuple[str, ...]:
        """前缀列举，排序返回（GR-18 确定性）。"""
        ...

    def require_keys(self, keys: Iterable[str]) -> None:
        """失联键闭环执行面：缺任一键 = 实现方领域异常。"""
        ...


@dataclass(frozen=True)
@final
class EngineParam:
    """引擎技术参数条目：值 + 出处 + 说明（UF-08；GR-15 出处门槛同向）。"""

    value: float
    source: str
    note: str

    def __post_init__(self) -> None:
        """value 非 bool/有限归一 float（GR-02）；source/note 非空 str。"""
        if isinstance(self.value, bool) or not isinstance(self.value, int | float):
            raise InvalidRunEnvError(
                f"EngineParam.value 必须为数值（int|float，bool 拒）："
                f"得到 {self.value!r}（GR-02 输入即拒）"
            )
        try:
            number = float(self.value)
        except OverflowError as exc:
            raise InvalidRunEnvError(
                f"EngineParam.value 超出浮点域：原值类型 "
                f"{type(self.value).__name__}（GR-02 输入即拒）"
            ) from exc
        if not isfinite(number):
            raise InvalidRunEnvError(
                f"EngineParam.value 非有限：{number!r}（GR-02 输入即拒）"
            )
        object.__setattr__(self, "value", number)
        object.__setattr__(
            self, "source", _nonempty_str(self.source, "EngineParam.source")
        )
        object.__setattr__(
            self, "note", _nonempty_str(self.note, "EngineParam.note")
        )


@dataclass(frozen=True)
@final
class RunEnv:
    """执行环境上下文：装配一次、执行期只读（R1/R3，UF-31）。"""

    engine_version: str
    data_version: str
    assumptions: Mapping[str, float]
    coefficients: CoefficientsView
    price_book: Mapping[str, Any]
    trace_sink: TraceSink | None
    engine_params: Mapping[str, EngineParam]

    def __post_init__(self) -> None:
        """版本串非空 + 三个 Mapping 构造即快照（T3A-01；R3 注记）。"""
        object.__setattr__(
            self,
            "engine_version",
            _nonempty_str(self.engine_version, "RunEnv.engine_version"),
        )
        object.__setattr__(
            self,
            "data_version",
            _nonempty_str(self.data_version, "RunEnv.data_version"),
        )
        object.__setattr__(
            self, "assumptions", MappingProxyType(dict(self.assumptions))
        )
        object.__setattr__(
            self, "price_book", MappingProxyType(dict(self.price_book))
        )
        object.__setattr__(
            self, "engine_params", MappingProxyType(dict(self.engine_params))
        )

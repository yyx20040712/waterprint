"""约束求值族：布尔约束过滤（含 UI 覆盖）+ 约束带裕度列（批2a）。

输入:  枚举 DataFrame + 约束集（constraint_kb 迁移 34 条 + UI 临时覆盖）
输出:  可行子集 + 每行×每约束的通过矩阵（供 diagnose）+ margin_min 裕度列
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结；镜像测试 tests/solution/test_constraints.py）
#
# 【公开接口】
#   class Constraint(不可变)：key、表达式 DSL（受限比较式：
#      field_id 与常数的 </<=/>/>=/∈ 关系 + AND 组合）、
#      source（constraint_kb 键或 "ui:临时覆盖"）、severity
#      （contracts.Severity，默认 ERROR=硬性过滤）
#   apply_constraints(df, constraints) -> FilterResult
#   class FilterResult(不可变)：feasible（可行子集位置索引）、
#       pass_matrix（DataFrame 布尔矩阵，行=方案 列=约束）
#   class InvalidConstraintError(Exception)：DSL 非法（未知字段/
#       非法算符/非法常数/空表达式）——GR-11 族，本文件定义
#   band_of(expression) -> tuple[str, float, float] | None：同字段
#       双侧带界解析（批2a 裁决①——裕度真源=kb 已追认约束带；
#       非带形/退化带 low>=high=None——不产出裕度，与过滤面行为对称）
#   MARGIN_COLUMN: Final[str]（="margin_min"）：裕度列名单源常量（三接线
#       面 app/stage/本件统一引用——门一 N1 处置）
#   band_margin_column(frame, constraints) -> pandas.Series：margin_min
#       裕度列（批2a——枚举行对带形约束的归一距离 min(v−a,b−v)/(b−a)，
#       行级取最紧；无适用带=NaN；调用面=app.run_enumeration/
#       stage.evaluate_stage，与 apply_constraints 同一约束集同源）
#   class KbConstraint(不可变)：constraint: Constraint + unit_kinds:
#       tuple[str, ...]（kb 条目装载形态——app_maintenance kb 执法面消费，
#       uf61-axes 批 2026-10-02）
#   load_kb_constraints(path) -> tuple[KbConstraint, ...]：constraint_kb
#       constraints.json 装载正门（fail-fast 显式拒：缺文件/坏 JSON/entries
#       空表/any_fail 保留字〔回炉 R2——kb 汇总键命名域防护〕；逐条 DSL 校验
#       坏档 fail-visible；source=kb 键、severity=Severity(entry) 随行；
#       宽容面归 CLI/未来调用方——本装载器 fail-fast，standards 装载器
#       区分记档）
#   expression_fields(expression) -> tuple[str, ...]：DSL 子句字段去重
#       现序列举（kb 适用判据单源——_clauses 单源解析的公开投影）
#   BOUNDARY_CHECK_KIND: Final[str]（="boundary_check"）：kind 符号契约
#       单源常量（kbwire C5 单源化——app_maintenance 豁免镜像消费公开名，
#       禁本地双源对齐）
#
# 【行为规格】
#   R1 约束是数据：知识库 34 条（旧 constraint_hints 迁移；kb 1.6.1 实数
#      =11+12+2+1+8——FD 批勘正历史构想字样 51→21、批3b 2026-09-26 增
#      geometry_guard 8 条、margin-kb-20261001 增双侧带 5 条〔起草待认〕）
#      + UI 覆盖，
#      表达式走受限 DSL（白名单字段 ID 与运算符），禁止任意 Python
#      lambda 注入（安全与可序列化）。
#   R2 pass_matrix 必须完整产出（哪怕全 False）——diagnose 的输入，
#      禁止只返回可行集丢弃失败信息（否则无解诊断不可能）。
#   R3 UI 覆盖不落盘为代码：临时覆盖只在会话内（design 态可保存勾选，
#      表达式本体永远来自知识库数据）。
#   R4 约束求值向量化（numpy 布尔运算），万级行 <1s（§18.1 预算内）。
#
# 【DSL 口径】子句 = field_id OP 常数，OP ∈ {<, <=, >, >=, ∈}；组合 =
#   子句 " and " 连接（AND 语义）；∈ 右侧为方括号数档列表
#   [v1, v2, ...]。常数来自 Constraint 数据（R1），代码零数值注入；
#   常数原子有限性守卫（1e999→inf 拒，M-3 R1 轮补——grid._number
#   同口径）。pass_matrix 列名 = 约束表达式串（锁定测试口径——列名即
#   约束的可读展开，diagnose 侧调用方按表达式串对账约束键）。
#   severity 执法口径（批5 统一定版——audit AUD-W10）：勾选/传入约束
#   一律硬过滤参与 feasible（CP1 用户裁决 2026-08-31「勾选=过滤」产品
#   语义——用户显式勾选即自愿升级为强制，与 kb「WARN=建议带」分类
#   并行不悖）；severity=随行元数据（装配面批5 起不再丢弃——kb 数据
#   值直传 Constraint.severity，审计/呈现面可依赖）。WARN 软语义（越
#   带注记不滤的未勾选默认态）=**显式不做**（2026-09-28 用户裁决·relay
#   增补六十三——越带几何量〔如超大单池〕属应滤除设计，工程正解=上调
#   池数而非单池做大，注记保留无价值；登记锚=UF-54 已闭合），勾选即
#   硬滤全级别为定版口径，本件不静默自定执法分级。
#
# 【测试要求】布尔矩阵正确性（含全 False 用例）、UI 覆盖生效与还原、
#   非法表达式（未知字段/运算符）拒绝、迁移知识库样例条目可用。
#
# 【参照】重写计划 §5/§12.4；数据包 data/constraint_kb/README.md
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import re
from ast import literal_eval
from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Final, final

import pandas  # type: ignore[import-untyped]  # pandas-stubs 未随包分发（M2-SOL 记档）

from waterprint.contracts.unit_api import Severity

_AND_SPLIT: re.Pattern[str] = re.compile(r"\s+and\s+")
_CLAUSE: re.Pattern[str] = re.compile(
    r"^(?P<field>[A-Za-z_][A-Za-z0-9_]*)\s*(?P<op><=|>=|<|>|∈)\s*(?P<value>.+)$"
)
_NUMBER: re.Pattern[str] = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
_LIST: re.Pattern[str] = re.compile(r"^\[(?P<items>.+)\]$")
_BAND_CLAUSE_COUNT: Final[int] = 2  # 带形=恰两子句（一侧下界一侧上界——批2a）


class InvalidConstraintError(Exception):
    """约束 DSL 非法（未知字段/非法算符/非法常数/空表达式）——GR-11 族。"""


@dataclass(frozen=True)
@final
class Constraint:
    """单条布尔约束（不可变）：键 + 受限 DSL 表达式 + 出处 + 级别。"""

    key: str
    expression: str
    source: str
    severity: Severity = Severity.ERROR

    def __post_init__(self) -> None:
        """key/expression/source 非空 str 守卫（R1 数据面准入）。"""
        for name in ("key", "expression", "source"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise InvalidConstraintError(
                    f"Constraint.{name} 必须为非空字符串：得到 {value!r}"
                )


def _atom(text: str, where: str) -> float:
    """单数值原子守卫（DSL 右值最小单元；有限性同 grid._number 口径）。"""
    stripped = text.strip()
    if not _NUMBER.match(stripped):
        raise InvalidConstraintError(
            f"{where} 须为数值：得到 {stripped!r}（R1 受限 DSL）"
        )
    number = float(stripped)
    if not isfinite(number):  # M-3（R1 轮修）："1e999"→inf 恒真/恒假约束禁入
        raise InvalidConstraintError(
            f"{where} 非有限：{stripped!r} → {number!r}（GR-02 输入即拒）"
        )
    return number


def _constant(text: str, where: str) -> float | tuple[float, ...]:
    """DSL 右值归一：数值或方括号数档列表（常数来自数据，代码零注入）。"""
    stripped = text.strip()
    listed = _LIST.match(stripped)
    if listed is None:
        return _atom(stripped, where)
    try:
        parsed = literal_eval(stripped)
    except (ValueError, SyntaxError) as exc:
        raise InvalidConstraintError(
            f"{where} 的档位列表非法：{stripped!r}（{exc}）"
        ) from exc
    if not isinstance(parsed, tuple | list) or not parsed:
        raise InvalidConstraintError(
            f"{where} 的档位列表须非空：{stripped!r}（GR-14 空集显式语义）"
        )
    return tuple(
        _atom(str(item), f"{where} 档位[{position}]")
        for position, item in enumerate(parsed)
    )


def _clauses(expression: str) -> tuple[tuple[str, str, float | tuple[float, ...]], ...]:
    """表达式 → 子句树（field, op, 常数）元组；语法/算符非法即拒。"""
    parts = [part for part in _AND_SPLIT.split(expression.strip()) if part]
    if not parts:
        raise InvalidConstraintError(f"约束表达式为空或仅含 and：{expression!r}")
    parsed: list[tuple[str, str, float | tuple[float, ...]]] = []
    for clause in parts:
        match = _CLAUSE.match(clause.strip())
        if match is None:
            raise InvalidConstraintError(
                f"约束子句语法非法：{clause!r}（形如 field_id (</<=/>/>=/∈) 常数，"
                "子句间以 and 组合——R1 受限 DSL）"
            )
        parsed.append(
            (
                match.group("field"),
                match.group("op"),
                _constant(match.group("value"), f"子句 {clause!r}"),
            )
        )
    return tuple(parsed)


def _evaluate(
    df: pandas.DataFrame, clauses: tuple[tuple[str, str, float | tuple[float, ...]], ...]
) -> pandas.Series:
    """numpy 布尔运算求值（R4 向量化）：未知字段即拒（消息含合法列）。"""
    columns = tuple(df.columns)
    combined: pandas.Series | None = None
    for field_id, op, constant in clauses:
        if field_id not in df.columns:
            raise InvalidConstraintError(
                f"约束引用未知字段 {field_id!r}（合法列 {list(columns)}——"
                "R1 DSL 白名单：字段须为枚举结果列/注册字段 ID）"
            )
        series = df[field_id]
        if op == "<":
            mask = series < constant
        elif op == "<=":
            mask = series <= constant
        elif op == ">":
            mask = series > constant
        elif op == ">=":
            mask = series >= constant
        else:
            mask = series.isin(constant)
        combined = mask if combined is None else combined & mask
    assert combined is not None  # 子句非空已在 _clauses 守卫
    return combined


def band_of(expression: str) -> tuple[str, float, float] | None:
    """表达式 → 同字段双侧带界（field, low, high）；非带形=None。

    带形判据（批2a 裁决①——「x >= a and x <= b 结构化解析带界」）：恰两
    子句、同一 field、一侧下界（>=/>）一侧上界（<=/<）、右值为数值（∈ 档
    列表无带宽概念非带）。单侧/跨字段/同向双子句/单子句=None（裕度覆盖面
    随 kb 扩条渐进）。退化带 low>=high 亦=None（门一 W1 处置：该带无带宽
    概念不产出裕度——与 apply_constraints 行为对称，恒不可行带由过滤面
    自然产出空集、low==high 单点带可行域不受误杀；裕度面不引入任务级
    行为回归）。
    """
    clauses = _clauses(expression)
    if len(clauses) != _BAND_CLAUSE_COUNT:
        return None
    (field_a, op_a, value_a), (field_b, op_b, value_b) = clauses
    if field_a != field_b or isinstance(value_a, tuple) or isinstance(value_b, tuple):
        return None
    if op_a in (">=", ">") and op_b in ("<=", "<"):
        low, high = float(value_a), float(value_b)
    elif op_a in ("<=", "<") and op_b in (">=", ">"):
        low, high = float(value_b), float(value_a)
    else:
        return None
    if low >= high:
        return None  # 退化带不产出裕度（docstring 口径——过滤面行为对称）
    return field_a, low, high


@dataclass(frozen=True)
@final
class FilterResult:
    """过滤产出（不可变）：可行子集位置索引 + 行×约束布尔通过矩阵。"""

    feasible: tuple[int, ...]
    pass_matrix: pandas.DataFrame


def apply_constraints(
    df: pandas.DataFrame, constraints: Sequence[Constraint]
) -> FilterResult:
    """过滤正门：逐约束向量化求值（列名=表达式串）→ 可行索引 + 完整矩阵。

    约束空集合法=全可行（本批约束由调用方传入；constraint_kb 21 条
    迁移 0.0.0→1.0.0 不属本批——独立数据批挂账）。
    """
    columns: dict[str, pandas.Series] = {}
    for constraint in constraints:
        columns[constraint.expression] = _evaluate(df, _clauses(constraint.expression))
    matrix = pandas.DataFrame(columns, index=df.index)
    if constraints:
        feasible = tuple(
            int(index) for index in matrix.all(axis=1).to_numpy().nonzero()[0]
        )
    else:
        feasible = tuple(range(len(df)))  # 空约束集=全可行（GR-14 显式语义）
    return FilterResult(feasible=feasible, pass_matrix=matrix)


_MARGIN_COLUMN: str = "margin_min"  # 公开别名 MARGIN_COLUMN（三接线面单源——门一 N1 处置）
MARGIN_COLUMN: Final[str] = _MARGIN_COLUMN


def band_margin_column(
    frame: pandas.DataFrame, constraints: Sequence[Constraint]
) -> pandas.Series:
    """裕度列正门（批2a 裁决①）：逐带向量化归一距离 → 行级最紧。

    R1 裕度语义=归一距离 min(v−a, b−v)/(b−a)：可行行 ∈[0, 0.5]（带缘 0、
    带中心 0.5）；越带行为负（随后被约束过滤剔除，负值不留消费面）。
    R2 行级取最紧：多带适用取 min（最紧指标优先——与旧 margin_* 字段
    语义同口径）；无适用带=NaN（「无裕度信息」诚实语义，stage 侧 NaN
    防护兜底）。
    R3 数值零新增：带界全部来自 kb 已追认表达式（band_of 解析）；非带形
    （单侧/∈/跨字段）不产出裕度——覆盖面随 kb 扩条渐进；带字段不在枚举
    行列=不适用（字段合法性由 apply_constraints 统一执法本函数不重复判）。
    R4 向量化：逐带 Series 运算+横向 min（万级行 <1s——apply 同预算口径）；
    域拒行（字段 NaN）距离 NaN，skipna 语义下仅全部适用带 NaN 才 NaN
    （行可行性仍由 nan_flag 双源口径承载）。
    """
    margins: list[pandas.Series] = []
    for constraint in constraints:
        band = band_of(constraint.expression)
        if band is None or band[0] not in frame.columns:
            continue  # 非带形/字段不适用=无裕度贡献（R3 覆盖面渐进）
        field, low, high = band
        series = frame[field]
        distance = pandas.concat([series - low, high - series], axis=1).min(axis=1)
        margins.append(distance / (high - low))
    if not margins:
        return pandas.Series(float("nan"), index=frame.index, name=_MARGIN_COLUMN)
    return pandas.concat(margins, axis=1).min(axis=1).rename(_MARGIN_COLUMN)


# ── kb 装载器域（uf61-axes 批 2026-10-02——app_maintenance kb 执法面）──────

# boundary_check=SPC2 §2.3 符号契约（containment == inside 固定式——非比较
# DSL 域，severity 解析面=server services/site.py）；kbwire C5 起公开单源
# （app_maintenance 豁免镜像消费公开名——本地双源对齐退役）
BOUNDARY_CHECK_KIND: Final[str] = "boundary_check"
_ANY_FAIL_KEY: Final[str] = "any_fail"  # kb 保留字（回炉 R2——face 汇总键命名域防护）


@dataclass(frozen=True)
@final
class KbConstraint:
    """kb 条目装载形态（不可变）：Constraint + 适用 unit_kinds 白名单 + kind
    （回炉 R2——boundary_check 豁免镜像的消费面判据；source/severity 不变）。"""

    constraint: Constraint
    unit_kinds: tuple[str, ...]
    kind: str


def expression_fields(expression: str) -> tuple[str, ...]:
    """DSL 子句字段去重现序列举（kb 适用判据单源——_clauses 单源投影）。"""
    seen: list[str] = []
    for field_id, _, _ in _clauses(expression):
        if field_id not in seen:
            seen.append(field_id)
    return tuple(seen)


def load_kb_constraints(path: str | Path) -> tuple[KbConstraint, ...]:
    """constraint_kb constraints.json 装载正门（fail-fast——uf61-axes 批）。

    三态显式拒+保留字拒（InvalidConstraintError 族，禁静默空表）：文件
    缺失/损坏 JSON/entries 空表/key=any_fail（回炉 R2）；装载期逐条 DSL 校验（_clauses parse——坏档
    fail-visible，消费面零延迟爆；boundary_check 例外=SPC2 §2.3 契约
    固定符号式 containment == inside，非比较 DSL 域——其 severity 解析
    面=server services/site.py，本装载器不重复执法）。source=kb 键、
    severity 随行；unit_kinds=[] 合法（boundary_check 全构筑物语义），
    其余 kind 空表的数据面门禁归 kb 数据批——本装载器不裁（回炉 R10）；
    宽容面（缺字段的个别条目跳过等）归 CLI/未来调用方——本装载器
    fail-fast，standards 装载器区分记档。

    装载宽容面记档（kbwire C5）：key/expression/source/kind 经 str() 强转
    =装载宽容非拒判；非缺文件 OSError（权限等）原生传播=环境面错误。
    """
    target = Path(path)
    if not target.is_file():
        raise InvalidConstraintError(
            f"constraint_kb 文件缺失：{target}（装载 fail-fast——禁静默空表）"
        )
    try:
        raw = json.loads(target.read_bytes())
    except ValueError as exc:
        raise InvalidConstraintError(
            f"constraint_kb JSON 解析失败：{target}（{exc}）"
        ) from exc
    entries = raw.get("entries") if isinstance(raw, dict) else None
    if not isinstance(entries, list) or not entries:
        raise InvalidConstraintError(
            f"constraint_kb entries 须为非空列表：{target}（GR-14 空集显式语义）"
        )
    loaded: list[KbConstraint] = []
    for position, item in enumerate(entries):
        if not isinstance(item, dict):
            raise InvalidConstraintError(
                f"constraint_kb entries[{position}] 须为对象：{item!r}（GR-02）"
            )
        try:
            constraint = Constraint(
                key=str(item["key"]),
                expression=str(item["expression"]),
                source=str(item["key"]),
                severity=Severity(str(item["severity"])),
            )
            kinds = item["unit_kinds"]
            if not isinstance(kinds, list):
                raise TypeError("unit_kinds 须为列表")
            unit_kinds = tuple(str(kind) for kind in kinds)
            kind = str(item["kind"])
        except (KeyError, TypeError, ValueError) as exc:
            raise InvalidConstraintError(
                f"constraint_kb entries[{position}] 字段缺失/非法"
                f"（key/expression/unit_kinds/severity/kind 必备）：{exc}"
            ) from exc
        if constraint.key == _ANY_FAIL_KEY:  # kb 保留字（回炉 R2）——命名域防护
            raise InvalidConstraintError(
                f"constraint_kb entries[{position}] key={_ANY_FAIL_KEY!r} 保留字"
                "（maint.<node>.kb.any_fail face 汇总键命名域防护——门禁前置装载面）")
        if kind != BOUNDARY_CHECK_KIND:
            _clauses(constraint.expression)  # 装载期 DSL 校验（fail-visible）
        loaded.append(KbConstraint(
            constraint=constraint, unit_kinds=unit_kinds, kind=kind))
    return tuple(loaded)

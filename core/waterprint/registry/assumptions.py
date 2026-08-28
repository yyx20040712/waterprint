"""设计假设清单唯一真源：一切默认值带出处与说明，UI 可查可改（§3 保证 7）。

输入:  假设声明（键/默认值/单位/出处/影响说明）
输出:  AssumptionSet（注入 UnitContext；项目可保存覆盖值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（T5 实现；镜像测试 tests/registry/test_assumptions.py）
#
# 【公开接口】
#   class TuningImpact(不可变)：direction: str（非空——调节方向短语，如
#       "增大超高→池体总高与造价上升"，供 §4 建议引擎展示）+
#       constraint_keys: tuple[str, ...]（构造期 Sequence 归一 tuple；
#       裸 str 拒——tuple() 会逐字符拆解为伪键，二审 I-2；归一后逐元素
#       须非空 str，消息含元素原值；空 tuple = 显式"无已知联动约束"
#       ——GR-14 空集声明：constraint_kb 现为 0.0.0 空槽，强填即编造）
#   class Assumption(不可变)：key: str / default: float /
#       dim: DimKey | str（构造期归一为 DimKey）/ source: str / note: str /
#       tuning_impact: TuningImpact | None = None
#       __post_init__ 六守卫（全走 InvalidAssumptionError，消息含
#       key+病因）：key 非空 str；default 非 bool 且有限（GR-02，归一
#       float）；dim 归一（非法字符串拒，消息含原值与合法成员）；
#       source/note 非空；tuning_impact 非 None（R2"缺一不可"——锁定
#       用例不传该参数实现序中先被 tuning_impact 守卫拒；两守卫同族
#       异常，顺序无关语义完整）
#   class AssumptionSet(不可变)：内部 items: tuple[Assumption, ...]
#       （私有字段 _items；Sequence 协议 __iter__/__getitem__(int)/
#       __len__——DEFAULT_ASSUMPTIONS[0] 与迭代即依赖）；构造期 Sequence
#       归一 tuple + 重复 key 拒；keys() -> tuple[str, ...] 排序返回
#   DEFAULT_ASSUMPTIONS: Final[AssumptionSet]
#       启动加载的默认清单（5 条：[0] safety.superheight 种子条目 +
#       loop.* 引擎参数三条 + solution.grid.base_per_dim 网格护栏基数
#       一条，见【种子条目】/【UF-08 引擎参数条目】/【网格护栏条目】）
#   assumption(key: str, overrides: Mapping[str, float]) -> float
#       取值正门：键未登记 = InvalidAssumptionError（禁静默默认——
#       魔法数借道路径）；命中 → overrides 有值用覆盖（覆盖值非 bool/
#       非数值/非有限 → InvalidAssumptionError 消息含 key+值，GR-02），
#       否则默认值；overrides 非 Mapping → 原生 TypeError（GR-08 程序
#       缺陷口径，非领域异常）
#   class InvalidAssumptionError(Exception)
#       登记与取值一切拒绝的统一载体（GR-11 族）
#
# 【行为规格】
#   R1 一切设计默认假设只允许存在于此（如污泥密度、安全超高、最小池深、
#      曝气器氧利用率等）；单元代码禁止内联默认数值，必须经
#      ctx.assumptions 取得——机器强制见 scripts/check_magic_numbers.py
#      （代码数值字面量白名单门禁），违反即 CI 失败。
#   R2 每条假设必须带出处与说明；无出处不准入库（与公式 norm_ref 同门槛）；
#      无 tuning_impact 的条目同样拒绝（初始参数不保证可行，诊断建议
#      依赖该元数据给出方向与幅度——business-logic.md §4）。
#   R3 项目文件保存"假设覆盖"进 design 态（参与 content_hash）——
#      改假设 = 改输入 = 结果过期（§12.3）。
#   R4 UI 可查可改：server 层提供清单读写端点，本文件是唯一数据源。
#
# 【种子条目】（T5 D5 数值红线裁决 2026-08-24——唯一合法路径）
#   恰 1 条 safety.superheight（dim=LENGTH）：default 值与 source 串
#   逐字取自 data/coefficients/factors.yaml 的 factor.screen.superheight
#   条目（0.1.0 已签字批次 2026-08-23——旧系统交叉基线+GB50014 注释引、
#   条文号待核对）；note 声明双真源关系与升版同步义务；tuning_impact:
#   direction="增大超高→池体总高与造价上升"、constraint_keys=()（显式
#   无已知联动）。依据：锁定测试要求 [0] 可取（空清单=IndexError 不可
#   行）；数值红线禁编造——值只能来自已签材料；三张已签手算表（CG-F9/
#   XG-F9/CS-F13 超高 0.3m）与签字系数包同源。
#   【T5 注记】assumptions_source.yaml 不创建（README 规划件，随后续
#   假设数据批落库）；本文件除种子条目外零数值面（数值纪律）。
#
# 【UF-08 引擎参数条目】（T7a D2 数值双闭案冻结 2026-08-25）
#   三条引擎参数以 assumptions 注册表条目入库（loop.py 规格明文
#   "tolerance 默认来自 assumptions"；本规格 R1 允许 source=工程惯例
#   类——引擎算法参数无规范条文可引）：loop.tolerance=1e-10（相对
#   残差，与锁定测试基准同量级）、loop.max_iterations=200（2+k 工况
#   性能预算内安全上界）、loop.damping=0.8（ADR-003 R3"阻尼默认
#   开启"）。app 装配（T7b）从 DEFAULT_ASSUMPTIONS 提取 loop.* 三键
#   投影 EngineParam 构造 RunEnv.engine_params——数值真源唯一在此，
#   禁散落代码字面量（GR-15）。registry 白名单区数值合法（门禁无
#   冲突）。DEFAULT_ASSUMPTIONS 1→4 条，safety.superheight 仍居
#   [0]（锁定用例依赖）。
#
# 【铁律】四注册表彼此独立互不 import（registry/__init__ 规格头）——
#   dim 归一在本文件自写同款私有函数，不许 import formulas/dimensions
#   的 _normalize_dim（B4 双胞胎代价先例在册）；本文件只依赖 L0
#   contracts.quantity 的 DimKey（L1→L0 合法边）。
#
# 【测试要求】覆盖优先级（项目覆盖>默认）、无出处登记拒绝、
#   未知键取值抛领域异常、默认清单全部带出处与说明。
#
# 【参照】重写计划 §3-7/§6.7；病灶"102.0m/3.0m/0.2m/4000 散落各处"；
#   简报 T5 D3/D4/D5/D6
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from math import isfinite
from typing import Final, final

from waterprint.contracts.quantity import DimKey


class InvalidAssumptionError(Exception):
    """假设登记/取值非法（守卫拒绝/未知键/覆盖值非法）——领域异常。"""


def _nonempty_str(value: object, what: str) -> str:
    """非空 str 守卫：类型不符/空串均拒，消息含字段名+原值。"""
    if not isinstance(value, str) or not value:
        raise InvalidAssumptionError(f"{what} 必须为非空字符串：得到 {value!r}")
    return value


def _normalize_dim(value: DimKey | str, key: str) -> DimKey:
    """D3 归一：DimKey | str → DimKey（非法字符串拒，消息含原值+合法成员）。

    双胞胎注记：与 dimensions/formulas 各自持有同款私有函数——四注册表
    彼此独立互不 import（registry/__init__ 铁律），禁跨文件复用私有名。
    """
    if isinstance(value, DimKey):
        return value
    if not isinstance(value, str):
        raise InvalidAssumptionError(
            f"假设 {key!r} 的 dim 必须为 DimKey 或其成员名字符串：得到 {value!r}"
        )
    try:
        return DimKey(value)
    except ValueError as exc:
        members = sorted(member.value for member in DimKey)
        raise InvalidAssumptionError(
            f"假设 {key!r} 的 dim 非法：{value!r}（合法 {members}）"
        ) from exc


def _normalize_number(value: object, key: str, what: str) -> float:
    """数值守卫（GR-02）：bool 拒/非数值拒/非有限拒，归一 float。"""
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidAssumptionError(
            f"假设 {key!r} 的 {what} 必须为数值（int|float，bool 拒）：得到 {value!r}"
        )
    try:
        number = float(value)
    except OverflowError as exc:
        raise InvalidAssumptionError(
            f"假设 {key!r} 的 {what} 超出浮点域：原值类型 {type(value).__name__}"
            "（GR-02 输入即拒；ARCH1 D1 同款——原生异常收编）"
        ) from exc
    if not isfinite(number):
        raise InvalidAssumptionError(f"假设 {key!r} 的 {what} 非有限：{number!r}（GR-02 输入即拒）")
    return number


@dataclass(frozen=True)
@final
class TuningImpact:
    """调节影响元数据（§4/§9 五字段的两个结构字段）：方向 + 联动约束键。"""

    direction: str
    constraint_keys: tuple[str, ...]

    def __post_init__(self) -> None:
        """direction 非空；裸 str 拒（I-2）；归一后逐元素非空 str；归一 tuple。"""
        if isinstance(self.constraint_keys, str):
            raise InvalidAssumptionError(
                f"TuningImpact.constraint_keys 必须为键序列（tuple/list），"
                f"不接受裸 str（会被逐字符拆解为伪键）：得到 {self.constraint_keys!r}"
            )
        _nonempty_str(self.direction, "TuningImpact.direction（调节方向短语，§4 建议引擎展示）")
        normalized = tuple(self.constraint_keys)
        for element in normalized:
            if not isinstance(element, str) or not element:
                raise InvalidAssumptionError(
                    f"TuningImpact.constraint_keys 元素必须为非空 str：得到 {element!r}"
                )
        object.__setattr__(self, "constraint_keys", normalized)


@dataclass(frozen=True)
@final
class Assumption:
    """单条设计假设：键 + 默认值 + 量纲 + 出处 + 说明 + 调节影响（六字段）。"""

    key: str
    default: float
    dim: DimKey | str
    source: str
    note: str
    tuning_impact: TuningImpact | None = None

    def __post_init__(self) -> None:
        """六守卫（全走 InvalidAssumptionError，消息含 key+病因）+ 归一。"""
        key = _nonempty_str(self.key, "假设 key")
        if self.tuning_impact is None:
            raise InvalidAssumptionError(
                f"假设 {key!r} 缺 tuning_impact（R2 缺一不可——初始参数不保证"
                "可行，诊断建议引擎依赖该元数据给出方向与幅度，business-logic"
                " §4）"
            )
        object.__setattr__(self, "key", key)
        object.__setattr__(self, "default", _normalize_number(self.default, key, "default"))
        object.__setattr__(self, "dim", _normalize_dim(self.dim, key))
        object.__setattr__(self, "source", _nonempty_str(self.source, f"假设 {key!r} 的 source"))
        object.__setattr__(self, "note", _nonempty_str(self.note, f"假设 {key!r} 的 note"))


@dataclass(frozen=True)
@final
class AssumptionSet:
    """假设清单只读集合：Sequence 协议 + keys()；构造期重复 key 拒。"""

    _items: tuple[Assumption, ...]

    def __post_init__(self) -> None:
        """items Sequence 归一 tuple + 重复 key 拒（键=取值正门唯一索引）。"""
        checked: list[Assumption] = []
        seen: set[str] = set()
        for item in self._items:
            if item.key in seen:
                raise InvalidAssumptionError(
                    f"假设键重复：{item.key!r}（AssumptionSet 内键唯一——"
                    "取值正门按键索引，重复=装配缺陷）"
                )
            seen.add(item.key)
            checked.append(item)
        object.__setattr__(self, "_items", tuple(checked))

    def __iter__(self) -> Iterator[Assumption]:
        """Sequence 协议：迭代（锁定用例依赖）。"""
        return iter(self._items)

    def __getitem__(self, index: int) -> Assumption:
        """Sequence 协议：整数下标取条目（锁定用例 DEFAULT_ASSUMPTIONS[0]）。"""
        return self._items[index]

    def __len__(self) -> int:
        """Sequence 协议：条目数。"""
        return len(self._items)

    def keys(self) -> tuple[str, ...]:
        """键清单，排序返回（GR-18 确定性）。"""
        return tuple(sorted(item.key for item in self._items))


def assumption(key: str, overrides: Mapping[str, float]) -> float:
    """取值正门（R1 根治点）：覆盖值优先，否则默认值；未知键 = 领域异常。

    禁止散落魔法数——病灶 102.0m/3.0m/0.2m/4000 的唯一合法取值通道；
    overrides 非 Mapping = 原生 TypeError（GR-08 程序缺陷口径）。
    """
    if not isinstance(overrides, Mapping):
        raise TypeError(
            f"overrides 必须为 Mapping[str, float]：得到 {type(overrides).__name__}"
            "（GR-08 程序缺陷口径——原生 TypeError，非领域异常）"
        )
    for item in DEFAULT_ASSUMPTIONS:
        if item.key == key:
            if key in overrides:
                return _normalize_number(overrides[key], key, "覆盖值")
            return item.default
    raise InvalidAssumptionError(
        f"未登记假设：{key!r}（合法假设见 DEFAULT_ASSUMPTIONS——禁止静默默认，"
        "魔法数借道路径；R1 一切默认假设只允许存在于此）"
    )


# ── 默认清单种子（D5 数值红线：default 与 source 逐字取自已签字数据包）──
# data/coefficients/factors.yaml 的 factor.screen.superheight 条目
# （0.1.0 已签字批次 2026-08-23）——双真源关系以 note 显式声明，
# 条文核对完成后随数据批同步升版（本文件唯一数值面）。
_SUPERHEIGHT: Final[Assumption] = Assumption(
    key="safety.superheight",
    default=0.3,
    dim=DimKey.LENGTH,
    source=(
        "旧系统 mod v5.1.0 交叉基线（栅后总高 H = h + h1 + 0.3）；"
        "dimension_formulas 注释引 GB50014 超高≥0.3m，条文号待核对原文"
    ),
    note=(
        "跨单元安全超高默认；与 factor.screen.superheight 同源同值"
        "（2026-08-23 签字批次）——单元专属档位仍走系数库键，"
        "条文核对完成后随数据批同步升版"
    ),
    tuning_impact=TuningImpact(
        direction="增大超高→池体总高与造价上升",
        constraint_keys=(),
    ),
)

# ── UF-08 引擎参数三条（T7a D2 冻结 2026-08-25：source=工程惯例类，
#    数值真源唯一在此；app 装配 T7b 提取 loop.* 三键投影 EngineParam
#    构造 RunEnv.engine_params，消费方 graph/loop.py 经 env 取用）──
_ENGINE_SOURCE: Final[str] = "UF-08/ADR-003 算法参数（总控 T7a 冻结 2026-08-25，工程惯例类）"
_LOOP_TOLERANCE: Final[Assumption] = Assumption(
    key="loop.tolerance",
    default=1e-10,
    dim=DimKey.DIMENSIONLESS,
    source=_ENGINE_SOURCE,
    note=(
        "回路固定点迭代相对残差收敛判据默认值（与锁定测试基准同量级，"
        "工程惯例类——引擎算法参数无规范条文可引）；app 装配（T7b）提取"
        "本键投影 EngineParam 入 RunEnv.engine_params"
    ),
    tuning_impact=TuningImpact(
        direction="收紧容差→迭代更严但步数增多，放宽→早停有假收敛风险",
        constraint_keys=(),
    ),
)
_LOOP_MAX_ITERATIONS: Final[Assumption] = Assumption(
    key="loop.max_iterations",
    default=200,
    dim=DimKey.DIMENSIONLESS,
    source=_ENGINE_SOURCE,
    note=(
        "回路迭代步数上限（2+k 工况性能预算 §18.1 <5s 门禁内安全上界）；"
        "超限即 LoopDivergence 走发散诊断，禁静默截断"
    ),
    tuning_impact=TuningImpact(
        direction="增大上限→更耐慢收敛但耗时上升，减小→发散误报增多",
        constraint_keys=(),
    ),
)
_LOOP_DAMPING: Final[Assumption] = Assumption(
    key="loop.damping",
    default=0.8,
    dim=DimKey.DIMENSIONLESS,
    source=_ENGINE_SOURCE,
    note=(
        "回路迭代阻尼系数（ADR-003 R3：阻尼默认开启——x_new = "
        "(1-λ)·x_old + λ·f(x_old) 抑制强耦合回路振荡）；0 等效关闭，"
        "届时须显式覆盖并在方案文档记录"
    ),
    tuning_impact=TuningImpact(
        direction="增大阻尼→收敛更稳但步数增多，减小→更快但振荡风险上升",
        constraint_keys=(),
    ),
)

# ── 网格护栏条目（M2-SOL D1 裁决 2026-08-26）：重写计划 §12.4
#    "自由参数网格 ≤4^k"/ADR-005 的机器强制基数——solution/grid.py
#    构建期消费（total > base**k → GridTooLarge）；registry 白名单区
#    数值合法，出处入库。──
_GRID_BASE_PER_DIM: Final[Assumption] = Assumption(
    key="solution.grid.base_per_dim",
    default=4.0,
    dim=DimKey.DIMENSIONLESS,
    source="重写计划 §12.4（自由参数网格 ≤4^k）/ADR-005（枚举语义）——M2-SOL D1 裁决",
    note=(
        "枚举网格组合数护栏的每维基数上限（总组合 total > base**k 拒，"
        "GridTooLarge 附缩小步长/范围建议）；solution/grid.py 消费，"
        "数值真源唯一在此（GR-15）"
    ),
    tuning_impact=TuningImpact(
        direction="增大基数→允许更大网格但枚举耗时与内存上升，减小→护栏更严",
        constraint_keys=(),
    ),
)

# ── DRAFT 批几何/损失键（D7 起草 2026-08-26，数据策略 v2 工程常用范围
#    口径——AI 起草待领域专家追认；elevation.freeboard.default 不新增：
#    safety.superheight（0.3 m）已承担超高语义，复用不重复[去重裁决]）。
#    elevation.* 服务 elevation 子系统（壁厚/埋深告警/跌水阈值/损失公式
#    经验系数/提升管路概算几何），geometry.* 服务三维几何（池列间距）；
#    全部经 assumption()/ctx 视图取值，数值真源唯一在此。──
_DRAFT_GEO: Final[tuple[Assumption, ...]] = (
    Assumption(
        "elevation.wall_thickness",
        0.3,
        DimKey.LENGTH,
        "《给水排水设计手册（第 5 册 城镇排水）》水池构造（工程常用 0.2~0.4 m 档中值，待追认）",
        "钢筋混凝土水池壁厚概算默认（m）——elevation 埋深与三维池壁图元消费",
        TuningImpact("增大壁厚→结构占用与造价上升，减小→配筋与抗渗压力上升", ()),
    ),
    Assumption(
        "elevation.bury_depth.max",
        6.0,
        DimKey.LENGTH,
        "《给水排水设计手册（第 5 册 城镇排水）》构筑物埋深工程常用上限（起草，待追认）",
        "池底埋深告警阈值（m）——build_profile 超限产生 Warning（留用户决策）",
        TuningImpact("增大阈值→放深埋深接受度，减小→更早告警", ()),
    ),
    Assumption(
        "elevation.drop_threshold",
        1.0,
        DimKey.LENGTH,
        "重写计划 §14.2 跌水与提升行（'跌水 >1m 提示'口径）",
        "水面衔接跌水提示阈值（m）——evaluate_pumping 超限生成 drop_warnings",
        TuningImpact("增大阈值→仅更陡跌水告警，减小→更早提示消能需求", ()),
    ),
    Assumption(
        "elevation.losses.friction_lambda",
        0.025,
        DimKey.DIMENSIONLESS,
        "《给水排水设计手册（第 5 册 城镇排水）》管道水力计算（达西 λ 0.02~0.03 档中值，待追认）",
        "沿程损失公式 EL-F1 的 λ 系数（无量纲）——losses.py 经 assumption() 取值，禁另抄",
        TuningImpact("增大 λ→损失与泵扬程上升，减小→偏乐观", ()),
    ),
    Assumption(
        "elevation.losses.gravity",
        9.81,
        DimKey.DIMENSIONLESS,
        "《给水排水设计手册（第 5 册 城镇排水）》水力计算重力加速度工程口径 9.81 m/s²",
        "损失公式族（EL-F1/F2/F4）速度水头分母 g（DIMENSIONLESS 裸值——单位随公式符号）",
        TuningImpact("工程口径固定值，不调节（登记仅为公式符号单一真源）", ()),
    ),
    Assumption(
        "elevation.losses.weir_coefficient",
        1.86,
        DimKey.DIMENSIONLESS,
        "《给水排水设计手册（第 3 册 城镇给水）》矩形薄壁堰流量系数 1.86（Q=m·b·h^1.5，待追认）",
        "堰流损失公式 EL-F3 的 m 系数（m^(3/2)/s 口径，DIMENSIONLESS 裸值登记）",
        TuningImpact("增大系数→同流量堰上水头下降，减小→偏保守", ()),
    ),
    Assumption(
        "elevation.losses.orifice_coefficient",
        0.62,
        DimKey.DIMENSIONLESS,
        "《给水排水设计手册（第 5 册 城镇排水）》孔口/管嘴出流流量系数 0.62（工程常用，待追认）",
        "孔口损失公式 EL-F4 的 μ 系数（无量纲）",
        TuningImpact("增大系数→同流量孔口损失下降，减小→偏保守", ()),
    ),
    Assumption(
        "elevation.pump.pipe_length",
        100.0,
        DimKey.LENGTH,
        "《给水排水设计手册（第 5 册 城镇排水）》泵站出水管概算管长工程常用档（起草，待追认）",
        "evaluate_pumping 提升管路损失概算管长（m）——实长归设计输入，M5 管线批接线",
        TuningImpact("增大管长→管路损失与总扬程上升", ()),
    ),
    Assumption(
        "elevation.pump.pipe_diameter",
        0.5,
        DimKey.LENGTH,
        "《给水排水设计手册（第 5 册 城镇排水）》泵站出水管概算管径工程常用档（起草，待追认）",
        "evaluate_pumping 提升管路损失概算管径（m）——设计输入接线前概算占位",
        TuningImpact("增大管径→流速与损失下降但造价上升", ()),
    ),
    Assumption(
        "geometry.pool.spacing",
        3.0,
        DimKey.LENGTH,
        "《给水排水设计手册（第 5 册 城镇排水）》并联池组检修通道/列间距工程常用档（待追认）",
        "三维并联池组排布列间距（m）——pools.py 消费，节点标注来源键",
        TuningImpact("增大间距→占地与连接管长上升，检修空间改善", ()),
    ),
)

# ── NET2 管网域引擎/安全面键（2026-08-28 段二批）：前四条数值逐字取自
#    已追认手算表 network_manning.md NM-F4 行（RATIFY4），后两条 §18 护栏（起草）──
_NM4_REF: Final[str] = "docs/norms/network_manning.md NM-F4（RATIFY4 追认 2026-08-28）"
_EXCEL_REF: Final[str] = "重写计划 §18 Excel zip 炸弹护栏（工程惯例类起草，待追认）"
_NETWORK: Final[tuple[Assumption, ...]] = (
    Assumption(
        "network.solve.tolerance", 1e-10, DimKey.FLOW,
        f"{_NM4_REF}：二分容差 |ΔQ|≤1e-10 m³/s（手算誊录精度 1e-4）",
        "solve_depth 停机判据（m³/s）——manning.py 消费",
        TuningImpact("收紧→迭代增多，放宽→早停假根风险", ()),
    ),
    Assumption(
        "network.solve.max_iterations", 200, DimKey.DIMENSIONLESS,
        f"{_NM4_REF}：最大 200 轮",
        "solve_depth 二分轮数上限——超限抛 NetworkHydraulicsError（禁静默截断）",
        TuningImpact("增大→更耐慢收敛，减小→不收敛误报增多", ()),
    ),
    Assumption(
        "network.solve.depth_min", 0.02, DimKey.DIMENSIONLESS,
        f"{_NM4_REF}：二分区间 [0.02, 0.998] 下端",
        "solve_depth 区间下端（h/D）",
        TuningImpact("抬高→浅流无解增多，降低→更稳", ()),
    ),
    Assumption(
        "network.solve.depth_max", 0.998, DimKey.DIMENSIONLESS,
        f"{_NM4_REF}：二分区间 [0.02, 0.998] 上端",
        "solve_depth 区间上端（h/D）",
        TuningImpact("抬升→近满流可解，降低→误报无解", ()),
    ),
    Assumption(
        "network.excel.max_rows", 5000, DimKey.DIMENSIONLESS,
        f"{_EXCEL_REF}——市政管网管段数百~数千段量级档",
        "read_network_excel 行数上限——超限抛 NetworkExcelError（只读解析前置防弹）",
        TuningImpact("增大→耗时与内存上升，减小→护栏更严", ()),
    ),
    Assumption(
        "network.excel.max_file_bytes", 10485760, DimKey.DIMENSIONLESS,
        f"{_EXCEL_REF}——10 MiB 档",
        "read_network_excel 文件大小上限（字节）——超限拒读",
        TuningImpact("增大→解压风险上升，减小→护栏更严", ()),
    ),
)

DEFAULT_ASSUMPTIONS: Final[AssumptionSet] = AssumptionSet(
    _items=(
        _SUPERHEIGHT,
        _LOOP_TOLERANCE,
        _LOOP_MAX_ITERATIONS,
        _LOOP_DAMPING,
        _GRID_BASE_PER_DIM,
        *_DRAFT_GEO,
        *_NETWORK,
    )
)

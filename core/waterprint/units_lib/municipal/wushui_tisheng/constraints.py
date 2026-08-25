"""污水提升泵房约束声明：键/表达式/出处/级别（声明式，限值经 factor 键引用）。

输入:  三表校核带（docs/norms/wushui_tisheng.md TS-F5/F10/F12）+ data/coefficients 0.4.0 带限键
输出:  CONSTRAINTS 声明表（供方案过滤与结果校核双消费，禁止内联数值）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（M2c 实装：表实合批的代码落地/M2 正式验收）
#
# 【固定形态】CONSTRAINTS: tuple[ConstraintDecl, ...] 模块级唯一常量；
#   每条：key / expression（受限比较式：结果字段或参数与 factor 键限值
#   比较）/ source（限值出处=data 包键 + 节级条文）/ severity。
# 【限值通道】三条校核带（出水管流速 0.7~1.5 m/s/水泵启停 ≤6 次/h/
#   集水井调节时间 5~15 min）数值真源=factor.wushui_tisheng.*（data
#   包 0.4.0，M2c 三单元系数批）——本文件零数值字面量，表达式按键
#   引用。单泵流量带（400~1500 m³/h）为选泵面校核、限值经概算锚
#   间接调节——仅 compute warnings 承载不在此声明；DN 档比阻表越表
#   为领域异常非警告带，不在声明。
# ══════════════════════════════════════════════════════════════════

from dataclasses import dataclass
from typing import final


@dataclass(frozen=True)
@final
class ConstraintDecl:
    """单条约束声明：键 + 受限比较式 + 出处 + 级别（声明式，无数值）。"""

    key: str
    expression: str
    source: str
    severity: str


_GB = "GB 50014-2021 §6.1（docs/norms/wushui_tisheng.md 起草表 2026-08-26，待追认）"
_HB = (
    "《给水排水设计手册（第 5 册 城镇排水）》泵站章；"
    "docs/norms/wushui_tisheng.md 起草表 2026-08-26，待追认"
)

CONSTRAINTS: tuple[ConstraintDecl, ...] = (
    ConstraintDecl(
        key="wushui_tisheng.pipe.velocity_band",
        expression=(
            "v_pipe_act >= factor.wushui_tisheng.pipe.velocity_band.min"
            " and v_pipe_act <= factor.wushui_tisheng.pipe.velocity_band.max"
        ),
        source=f"{_HB}；TS-F5 带宽（factor.wushui_tisheng.pipe.velocity_band.*，压力管经济流速）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="wushui_tisheng.pump.start_band",
        expression="n_start <= factor.wushui_tisheng.pump.start_band.max",
        source=f"{_HB}；TS-F12 上限（factor.wushui_tisheng.pump.start_band.max，水位启停频率）",
        severity="WARN",
    ),
    ConstraintDecl(
        key="wushui_tisheng.well.t_band",
        expression=(
            "t_well >= factor.wushui_tisheng.well.t_band.min"
            " and t_well <= factor.wushui_tisheng.well.t_band.max"
        ),
        source=(
            f"{_GB}；{_HB}；TS-F10 参数带"
            "（factor.wushui_tisheng.well.t_band.*，调节容积常用档）"
        ),
        severity="WARN",
    ),
)

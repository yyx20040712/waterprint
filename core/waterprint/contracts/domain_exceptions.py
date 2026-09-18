"""领域异常族核心元组：contracts 层四族单源（两消费面组合消费）。

输入:  无（纯常量聚合）
输出:  DOMAIN_EXCEPTIONS_CORE（行级域拒/整图隔离两捕获面的公共族真源）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（B3-c 批 2c 收敛 2026-09-19，三段通道定案=docs/design/
#   2026-09-19_b4-twins-convergence-design.md）：
#   executor._DOMAIN_EXCEPTIONS 与 enumerate._ROW_DOMAIN_EXCEPTIONS
#   两份人工同步收敛——交集四族（全部 contracts 层定义）单源于此；
#   两消费面组合式复现各自成员集（CORE+专属族，字节级恒等）。
#   同步义务新口径：新增 contracts 层领域异常族→改本元组（两消费面
#   自动同步）；新增 graph/registry 层族→改各消费面组合尾（语境专属，
#   无跨面同步义务）。已知 latent 不对称（executor 不含
#   InvalidFormulaError）挂账 G1 见定案 §6，本件不修。
# 【公开接口】
#   DOMAIN_EXCEPTIONS_CORE: Final[tuple[type[Exception], ...]]
# 【铁律】L0 零内部依赖——仅 import 同包四族定义位
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations

from typing import Final

from waterprint.contracts.flow import InvalidFlowError
from waterprint.contracts.manifest import InvalidUnitConfig
from waterprint.contracts.quality import InvalidQualityError
from waterprint.contracts.sludge import InvalidSludgeError

# 领域异常族公共核心（宪法 §3 禁裸/过宽捕获 → 显式元组收口）：
# 序=executor._DOMAIN_EXCEPTIONS 现相对序（Flow/Quality/Sludge/UnitConfig）。
DOMAIN_EXCEPTIONS_CORE: Final[tuple[type[Exception], ...]] = (
    InvalidFlowError, InvalidQualityError, InvalidSludgeError, InvalidUnitConfig,
)

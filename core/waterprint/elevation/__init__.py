"""L3 高程子系统包根：水头损失/沿程推算/提升判定（只消费结果契约）。

输入:  PlantResult（图结果）+ 高程输入配置（进厂水面标高等）
输出:  纵断数据与泵参数（profile 正门）
"""

# ══════════════════════════════════════════════════════════════════
# 规格说明（骨架冻结）
#
# 【导出白名单】
#   losses:  head_losses
#   profile: build_profile
#   pumps:   evaluate_pumping
# 边界：本子系统与其他 L3 互不 import（import-linter 独立契约）；
# 旧 jcws_smbg（进厂水面标高）与 gdys_stss（管道水头损失）模组折叠为
# 本子系统的输入配置，不再是单元包（§14.3 归属表）。
# ══════════════════════════════════════════════════════════════════

from waterprint.elevation.losses import head_losses
from waterprint.elevation.profile import build_profile
from waterprint.elevation.pumps import evaluate_pumping

__all__ = ["build_profile", "evaluate_pumping", "head_losses"]

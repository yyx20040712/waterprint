"""公式注册表子包聚合正门（b2-s2-formulas-package 拆自 formulas.py 机制件）。

批次: b2-s2-formulas-package

输入:  spec（规格声明+DSL 解析）/store（登记真源+静态校验）/apply
       （唯一求值正门）三机制件
输出:  改造前 formulas.py 全部无下划线公开名九名（D1-B：条目留
       manifest 原位，两种消费形态——命名空间/直名——均不断）
"""

# 聚合 import 三行（幂等哨兵之一）——书写序=ruff isort 字母序；依赖序
# spec←store←apply 经链式 import 隐式保持（apply 首行触发 store、store
# 触发 spec，三件全部急切加载后正门才就绪——§4.4 急切语义等价实现）。
# 注意：正门 re-export 使 formulas.apply 恒为函数（消费面零变），子模块
# 名被遮蔽——取子模块对象须 importlib.import_module（import…as 形态
# 会绑到函数）。
from waterprint.registry.formulas.apply import apply, apply_batch
from waterprint.registry.formulas.spec import FormulaSpec, InvalidFormulaError
from waterprint.registry.formulas.store import (
    ValidationReport,
    by_id,
    norm_ref_of,
    register,
    validate_all,
)

__all__ = [
    "FormulaSpec",
    "InvalidFormulaError",
    "ValidationReport",
    "apply",
    "apply_batch",
    "by_id",
    "norm_ref_of",
    "register",
    "validate_all",
]

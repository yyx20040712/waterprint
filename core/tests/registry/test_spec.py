"""公式规格件镜像测试（B2-5 拆分配套——[HUMAN-LOCK] 起草待批件）。

输入:  registry/formulas/spec.py 公开面
输出:  镜像存在性+导入冒烟（行为面主体由 tests/registry/test_formulas.py
       全量锁定——本件为镜像规则最小义务薄壳）
"""

from waterprint.registry.formulas import spec


def test_module_importable() -> None:
    """镜像规则最小义务：模块可导入+公开面在场。"""
    assert hasattr(spec, "FormulaSpec")
    assert hasattr(spec, "InvalidFormulaError")

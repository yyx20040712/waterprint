"""公式登记件镜像测试（B2-5 拆分配套——[HUMAN-LOCK] 起草待批件）。

输入:  registry/formulas/store.py 公开面
输出:  镜像存在性+导入冒烟（行为面主体由 tests/registry/test_formulas.py
       全量锁定——本件为镜像规则最小义务薄壳）
"""

from waterprint.registry.formulas import store


def test_module_importable() -> None:
    """镜像规则最小义务：模块可导入+公开面在场。"""
    for name in ("ValidationReport", "register", "by_id", "validate_all", "norm_ref_of"):
        assert hasattr(store, name)

"""公式求值件镜像测试（B2-5 拆分配套——[HUMAN-LOCK] 起草待批件）。

输入:  registry/formulas/apply.py 公开面
输出:  镜像存在性+导入冒烟（行为面主体由 tests/registry/test_formulas.py
       与 test_apply_face_baseline.py 锁定——本件为镜像规则最小义务薄壳）
"""

import importlib


def test_module_importable() -> None:
    """镜像规则最小义务：模块可导入+公开面在场。

    注意 import 形态：子包正门把函数 apply re-export 到 formulas 命名
    空间（消费面零变——formulas.apply 恒为函数），属性查找路径下子模块
    名被函数遮蔽，故须经 importlib（sys.modules 权威路径）取子模块对象。
    """
    module = importlib.import_module("waterprint.registry.formulas.apply")
    assert hasattr(module, "apply")
    assert hasattr(module, "apply_batch")

"""formulas.apply 面向量化重写前基线锚(批 13-A 基线先行独立笔)。

输入:  registry apply 标量正门——重写前树态(c97bd24ee8)拒绝路径
       消息+成功路径值域冻结(探针公式 B13A-* 本件登记,进程内
       唯一前缀;validate_all 无计数断言——tests/registry grep 实证
       零扰动)
输出:  消息恒等锚(R1 锚②公式面——重写后逐字恒等)+值域精确锚
"""

# ════════════════════════════════════════════════════════════
# 规格说明(批 13-A;task-13A-batch-plan §六;同款即绿注记——
# 生成器于重写前树态运行产出;4b 举证:tests/registry/test_
# formulas.py 仅 4 用例,零 apply 消息文本锚+零值域锚=apply 面
# 重写等价验收缺位)。溢出消息 {exc} 段=平台相依形态(Windows/
# Linux 措辞异)——沿重写前同平台同文,基线锚本机形态。
# ════════════════════════════════════════════════════════════

from __future__ import annotations

import pytest

from waterprint.contracts.quantity import DimKey
from waterprint.registry.formulas import FormulaSpec, InvalidFormulaError, apply, register

register(
    FormulaSpec(
        formula_id="B13A-ADD",
        expression="OUT = a + b",
        symbols={"a": (DimKey.LENGTH, "探针加数"), "b": (DimKey.LENGTH, "探针加数")},
        output_dim=DimKey.LENGTH,
        norm_ref="批13-A 基线探针(仅测试面)",
    )
)
register(
    FormulaSpec(
        formula_id="B13A-DIV",
        expression="OUT = a / b",
        symbols={"a": (DimKey.VOLUME, "探针被除数"), "b": (DimKey.LENGTH, "探针除数")},
        output_dim=DimKey.AREA,
        norm_ref="批13-A 基线探针(仅测试面)",
    )
)
register(
    FormulaSpec(
        formula_id="B13A-SQR",
        expression="OUT = a * a",
        symbols={"a": (DimKey.LENGTH, "探针边长")},
        output_dim=DimKey.AREA,
        norm_ref="批13-A 基线探针(仅测试面)",
    )
)

_CTX = ("b13a_face", "design")


def test_apply_reject_messages() -> None:
    """apply 拒绝路径消息逐字锚(类型+文本恒等——R1 锚②)。"""
    for formula_id, bindings, kind, message in [
        ('B13A-NONE',
         {
             'a': 1.0,
         },
         'InvalidFormulaError',
         "未登记公式：'B13A-NONE'（apply 只消费 register 登记项）"),
        ('B13A-ADD',
         {
             'a': 1.0,
             'c': 2.0,
         },
         'InvalidFormulaError',
         "公式 'B13A-ADD' 求值绑定键集与 symbols 键集不一致：缺 ['b']，多 ['c']（应恰为 ['a', 'b']"
         '）'),
        ('B13A-ADD',
         {
             'a': 1.0,
             'b': True,
         },
         'InvalidFormulaError',
         "公式 'B13A-ADD' 符号 'b' 的绑定值必须为数值：得到 True"),
        ('B13A-ADD',
         {
             'a': 1.0,
             'b': 'x',
         },
         'InvalidFormulaError',
         "公式 'B13A-ADD' 符号 'b' 的绑定值必须为数值：得到 'x'"),
        ('B13A-ADD',
         {
             'a': 1.0,
             'b': float("nan"),
         },
         'InvalidFormulaError',
         "公式 'B13A-ADD' 符号 'b' 的绑定值非有限：nan（GR-02 输入即拒）"),
        ('B13A-ADD',
         {
             'a': 1.0,
             'b': float("inf"),
         },
         'InvalidFormulaError',
         "公式 'B13A-ADD' 符号 'b' 的绑定值非有限：inf（GR-02 输入即拒）"),
        ('B13A-ADD',
         {
             'a': 1.0,
             'b': 10**400,
         },
         'InvalidFormulaError',
         "公式 'B13A-ADD' 符号 'b' 的绑定值超出浮点域：原值类型 int（GR-02 输入即拒；ARCH1 D1a——原"
         '生异常收编）'),
        ('B13A-DIV',
         {
             'a': 1.0,
             'b': 0.0,
         },
         'InvalidFormulaError',
         "公式 'B13A-DIV' 求值数值域错误（除零/溢出/定义域，expr R5 原生异常包装）：float division"
         ' by zero'),
        ('B13A-SQR',
         {
             'a': 1e+200,
         },
         'InvalidFormulaError',
         "公式 'B13A-SQR' 求值结果非有限：inf（GR-02 运算产生即转领域异常）"),
    ]:
        with pytest.raises(InvalidFormulaError) as excinfo:
            apply(formula_id, bindings, _CTX)
        assert type(excinfo.value).__name__ == kind
        assert str(excinfo.value) == message


def test_apply_success_values() -> None:
    """apply 成功路径值域精确锚(IEEE 位级——重写后恒等)。"""
    for formula_id, bindings, expected in [
        ('B13A-ADD',
         {
             'a': 0.1,
             'b': 0.2,
         },
         0.30000000000000004),
        ('B13A-DIV',
         {
             'a': 3.0,
             'b': 7.0,
         },
         0.42857142857142855),
        ('B13A-SQR',
         {
             'a': 94.2178,
         },
         8876.99383684),
    ]:
        assert apply(formula_id, dict(bindings), _CTX) == expected

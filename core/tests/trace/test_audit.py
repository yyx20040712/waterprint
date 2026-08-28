"""audit 镜像测试：审计报告（结构完整/转义/自包含/确定性/路径安全接线）。

输入:  waterprint.trace.audit 公开符号
输出:  报告契约断言
注记:  探针公式 M4-AUDIT-F1/F2 进程级注册持久（AUDIT 一审 M-2 防雷记档）：
       注册表无卸载正门（register 幂等容忍重复），将来任何"注册表键集
       穷尽"类断言须排除本文件探针键（专用前缀 M4-AUDIT-*，与正式键族
       隔离），否则将因测试顺序踩雷。
"""

from __future__ import annotations

import html
import importlib
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from waterprint.contracts.result_schema import TraceNode

_mod = importlib.import_module("waterprint.trace.audit")
render_audit_html = getattr(_mod, "render_audit_html", None)
InvalidAuditPathError = getattr(_mod, "InvalidAuditPathError", None)

pytestmark = pytest.mark.skipif(
    render_audit_html is None,
    reason="实现未就绪：waterprint.trace.audit（M4）",
)

_MALICIOUS_UNIT = "<script>alert(1)</script>"
_PROBE_FORMULAS = ("M4-AUDIT-F1", "M4-AUDIT-F2")
_PROBE_NORM_REF = "测试条文 M4-audit"


def _register_probe_formulas() -> None:
    """登记测试专用公式对（DimKey 全 DIMENSIONLESS；幂等容忍重复登记）。"""
    from waterprint.contracts.quantity import DimKey
    from waterprint.registry.formulas import (
        FormulaSpec,
        InvalidFormulaError,
        by_id,
        register,
    )

    for formula_id, symbol in zip(
        _PROBE_FORMULAS, ("x", "y"), strict=True
    ):
        try:
            by_id(formula_id)
            continue  # 已登记（同进程多测试共享注册表）
        except InvalidFormulaError:
            pass
        register(
            FormulaSpec(
                formula_id=formula_id,
                expression=f"{symbol} = a + b",
                symbols={
                    "a": (DimKey.DIMENSIONLESS, "测试符号 a"),
                    "b": (DimKey.DIMENSIONLESS, "测试符号 b"),
                },
                output_dim=DimKey.DIMENSIONLESS,
                norm_ref=_PROBE_NORM_REF,
            )
        )


def _trace() -> tuple[TraceNode, ...]:
    """最小迹树：2 单元×2 公式（其中 1 单元名为恶意注入探针，§18）。

    常规单元（design 工况）跑 F1+F2；恶意名单元（check 工况）跑 F1
    ——覆盖工况分章/单元分节/恶意转义三面。
    """
    from waterprint.contracts.result_schema import TraceNode

    return (
        TraceNode(
            formula_id="M4-AUDIT-F1",
            inputs={"a": 1.0, "b": 2.0},
            output=3.0,
            norm_ref=_PROBE_NORM_REF,
            unit_id="m4_normal_unit",
            condition_key="design",
        ),
        TraceNode(
            formula_id="M4-AUDIT-F2",
            inputs={"a": 10.0, "b": 20.0},
            output=30.0,
            norm_ref=_PROBE_NORM_REF,
            unit_id="m4_normal_unit",
            condition_key="design",
        ),
        TraceNode(
            formula_id="M4-AUDIT-F1",
            inputs={"a": 100.0, "b": 200.0},
            output=300.0,
            norm_ref=_PROBE_NORM_REF,
            unit_id=_MALICIOUS_UNIT,
            condition_key="check",
        ),
    )


def _result() -> object:
    """最小 PlantResult（汇总两工况；repro 三元组=R4 时间戳替代源）。"""
    from types import MappingProxyType

    from waterprint.contracts.result_schema import PlantResult, ReproTriple

    return PlantResult(
        conditions=MappingProxyType({}),
        summary=MappingProxyType(
            {
                "design": MappingProxyType({"total_sludge": 667.4}),
                "check": MappingProxyType({"total_sludge": 668.0}),
            }
        ),
        trace=(),
        repro=ReproTriple(
            design_hash="m4-audit", engine_version="m4", data_version="m4"
        ),
    )


def _render(tmp_path: Path) -> str:
    """渲染正门薄封装：登记探针公式→落盘→回读 HTML 文本。"""
    _register_probe_formulas()
    out = render_audit_html(_trace(), _result(), tmp_path / "audit.html")  # type: ignore[misc]
    assert isinstance(out, Path)
    return out.read_text(encoding="utf-8")


def test_entrypoint_frozen() -> None:
    """入口冻结：render_audit_html(trace, result, out)。"""
    assert callable(render_audit_html)


def test_escapes_user_controlled_text_wiring(tmp_path: Path) -> None:
    """R2 接线断言：恶意单元名（含 <script>）被转义——原始标签不出现。"""
    document = _render(tmp_path)
    assert _MALICIOUS_UNIT not in document  # 原始 <script>alert(1)</script> 不得出现
    assert html.escape(_MALICIOUS_UNIT) in document  # 转义形态 &lt;script&gt;… 在
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in document


def test_structure_complete_wiring(tmp_path: Path) -> None:
    """R1 接线断言：每公式条目含公式 ID/表达式/输入/输出+非空 norm_ref。"""
    document = _render(tmp_path)
    assert "公式溯源审计报告" in document
    assert html.escape("design") in document and html.escape("check") in document
    for node in _trace():
        assert node.norm_ref  # 每节点条文号非空（M4 验收前提）
        assert html.escape(node.formula_id) in document
        assert html.escape(node.norm_ref) in document
        assert html.escape("a + b") in document  # REGISTRY expression 面
        assert html.escape("测试符号 a") in document  # 符号定义面
        for key, value in node.inputs.items():  # inputs 逐键=值面（AUDIT 一审 M-1 收紧：单字符断言平凡通过）
            assert f"{html.escape(key)} = {value!r}" in document
        assert repr(node.output) in document  # value 输出
    assert repr(667.4) in document  # 汇总指标面值
    assert html.escape("total_sludge") in document  # 汇总来源字段 ID
    assert "m4-audit" in document  # repro 三元组（R4 时间戳替代源）


def test_self_contained_no_external_refs_wiring(tmp_path: Path) -> None:
    """R3 接线断言：内联 CSS、零外部 URL/脚本。"""
    document = _render(tmp_path)
    assert "<style>" in document  # 内联样式在
    assert "<script" not in document  # 零脚本
    assert "http://" not in document and "https://" not in document  # 零外部 URL
    assert "@import" not in document and "url(" not in document  # 零字体/资源引用


def test_deterministic_double_render_wiring(tmp_path: Path) -> None:
    """R4 接线断言：同迹树同结果双渲染字节相同（零当前时钟）。"""
    _register_probe_formulas()
    first = tmp_path / "first.html"
    second = tmp_path / "second.html"
    render_audit_html(_trace(), _result(), first)  # type: ignore[misc]
    render_audit_html(_trace(), _result(), second)  # type: ignore[misc]
    assert first.read_bytes() == second.read_bytes()  # 双跑字节级相等


def test_path_outside_rejected_wiring(tmp_path: Path) -> None:
    """R5 接线断言：相对路径与含 '..' 分量的输出路径拒绝（领域异常）。"""
    _register_probe_formulas()
    assert InvalidAuditPathError is not None  # getattr 兜底形态收窄（AUDIT M-3：tests 面 mypy）
    with pytest.raises(InvalidAuditPathError, match="绝对路径"):
        render_audit_html(_trace(), _result(), Path("relative.html"))  # type: ignore[misc]
    with pytest.raises(InvalidAuditPathError, match=r"\.\."):
        render_audit_html(_trace(), _result(), tmp_path / ".." / "escape.html")  # type: ignore[misc]


def test_print_media_wiring(tmp_path: Path) -> None:
    """打印版接线断言（M4a ⑤）：@media print 块关键选择器在。

    表头跨页重复（thead→table-header-group）+ 工况分章分页断点（首章
    除外——标题页与首章同页）+ 行/单元节不截断（page-break-inside）。
    渲染断言不强求视觉验证（选择器存在性=结构性证明）。
    """
    document = _render(tmp_path)
    assert "@media print" in document
    assert "table-header-group" in document  # 表头重复
    assert "page-break-before" in document  # 分页断点
    assert "page-break-inside" in document  # 行/单元节不跨页截断
    assert ":not(:first-of-type)" in document  # 首章豁免（标题页不断）

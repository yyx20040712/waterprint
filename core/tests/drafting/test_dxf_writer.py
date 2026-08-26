"""dxf_writer 镜像测试：ezdxf 唯一接触点（R2018/UTF-8/确定性/路径安全）。

输入:  waterprint.drafting.dxf_writer 公开符号
输出:  落盘契约断言
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint.drafting.dxf_writer")
write_dxf = getattr(_mod, "write_dxf", None)

pytestmark = pytest.mark.skipif(
    write_dxf is None,
    reason="实现未就绪：waterprint.drafting.dxf_writer（M2）",
)


def _group():
    from waterprint.drafting.styles import Entity, EntityGroup

    return EntityGroup(entities=(
        Entity("rect", "WP-process-pool", ((0.0, 0.0), (4.5, 3.0)),
               source_key="l_straight|d"),
        Entity("text", "WP-anno-label", ((4.5, -3.0),),
               text="condition=design 粗格栅 中文往返"),
    ))


def _meta():
    from waterprint.drafting.dxf_writer import DrawingMeta

    return DrawingMeta(title="粗格栅平面", condition_key="design",
                       repro=("hash", "engine", "data"))


def test_entrypoint_frozen() -> None:
    """入口冻结：write_dxf(entities, styles, out, meta)。"""
    assert callable(write_dxf)


def test_path_traversal_rejected_wiring(tmp_path: Path) -> None:
    """R4 接线断言（M2 实质化）：越界路径（../ 分量/相对路径）→ 领域异常。

    占位实质化（DRAFT 批总授权先例）：SERVER 教训 §18 路径安全——
    '..' 分量与相对路径两类越界均拒（InvalidDrawingPathError）。
    """
    from waterprint.drafting.dxf_writer import InvalidDrawingPathError
    from waterprint.drafting.styles import base_styles

    traversal = tmp_path / ".." / "escape.dxf"
    with pytest.raises(InvalidDrawingPathError):
        write_dxf(_group(), base_styles(), traversal, _meta())
    with pytest.raises(InvalidDrawingPathError):
        write_dxf(_group(), base_styles(), Path("relative/plan.dxf"), _meta())


def test_byte_determinism_wiring(tmp_path: Path) -> None:
    """R3 接线断言（M2 实质化）：同实体组双跑落盘字节级相同+R2018 头+UTF-8。

    占位实质化（DRAFT 批总授权先例）：双跑 write_dxf 字节 diff=0；ezdxf
    回读 $ACADVER==AC1032（R2018）且模型空间实体数>0、中文 TEXT 往返无损。
    """
    from waterprint.drafting.styles import base_styles

    first = write_dxf(_group(), base_styles(), tmp_path / "run1.dxf", _meta())
    second = write_dxf(_group(), base_styles(), tmp_path / "run2.dxf", _meta())
    assert first.read_bytes() == second.read_bytes()  # 双跑字节级相同
    import ezdxf

    doc = ezdxf.readfile(first)
    assert doc.dxfversion == "AC1032"  # R2018 版本头
    assert len(doc.modelspace()) > 0
    texts = [e.dxf.text for e in doc.modelspace() if e.dxftype() == "TEXT"]
    assert any("中文往返" in t for t in texts)  # UTF-8 中文往返


def test_scale_factor_halves_entity_size(tmp_path: Path) -> None:
    """R1-2（2026-08-26）比例接线：同实体组 1:100 vs 1:50 → 图幅尺寸比恰 2:1。"""
    from waterprint.drafting.styles import base_styles

    first = write_dxf(_group(), base_styles(), tmp_path / "s100.dxf", _meta())
    second = write_dxf(
        _group(), base_styles(), tmp_path / "s50.dxf", _meta(), scale="1:50"
    )
    import ezdxf

    def max_x(path: Path) -> float:
        doc = ezdxf.readfile(path)
        return max(
            max(x for x, _ in entity.get_points("xy"))
            for entity in doc.modelspace()
            if entity.dxftype() == "LWPOLYLINE"
        )

    ratio = max_x(second) / max_x(first)
    assert ratio == pytest.approx(2.0)  # 1:50 图幅恰为 1:100 的两倍


def test_audit_header_custom_vars_roundtrip(tmp_path: Path) -> None:
    """R1-4（2026-08-26，NF-1）审计头完整落盘：三元组+工况 custom_vars 可回读。"""
    from waterprint.drafting.styles import base_styles

    out = write_dxf(_group(), base_styles(), tmp_path / "audit.dxf", _meta())
    import ezdxf

    doc = ezdxf.readfile(out)
    custom = dict(doc.header.custom_vars)
    assert custom["condition_key"] == "design"
    assert custom["design_hash"] == "hash"
    assert custom["engine_version"] == "engine"
    assert custom["data_version"] == "data"  # 三元组不可再静默丢

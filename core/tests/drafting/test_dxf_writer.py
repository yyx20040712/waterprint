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


def _classes_blocks(data: bytes) -> list[tuple[bytes, ...]]:
    """产物 CLASSES 段记录块（组码 0 分界——CRLF 行对解析）。

    批 14-FIX 断言辅助：缺段/配对破缺抛 ValueError（畸形输入响失败）。
    """
    lines = data.split(b"\r\n")
    start = end = -1
    for i in range(len(lines) - 1):
        if lines[i].strip() == b"0" and lines[i + 1] == b"SECTION" \
                and i + 3 < len(lines) and lines[i + 2].strip() == b"2" \
                and lines[i + 3] == b"CLASSES":
            k = i + 4
            while k + 1 < len(lines) and not (
                lines[k].strip() == b"0" and lines[k + 1] == b"ENDSEC"
            ):
                k += 1
            if k + 1 >= len(lines):
                raise ValueError("CLASSES 段无 ENDSEC（畸形）")
            start, end = i + 4, k
            break
    if start < 0:
        raise ValueError("缺 CLASSES 段（畸形）")
    body = lines[start:end]
    if len(body) % 2 != 0:
        raise ValueError("CLASSES 段体行数非偶（配对破缺）")
    blocks: list[tuple[bytes, ...]] = []
    current: list[bytes] = []
    for i in range(0, len(body), 2):
        if body[i].strip() == b"0":
            if current:
                blocks.append(tuple(current))
            current = [body[i], body[i + 1]]
        else:
            current.extend((body[i], body[i + 1]))
    if current:
        blocks.append(tuple(current))
    return blocks


_SUBPROC_SCRIPT = (
    # 子进程经 -c 注入最小渲染链——依赖包可导入（core/.venv 安装态 /
    # PYTHONPATH 指向 core/；CI pytest 同解释器同 cwd 可满足——R 轮
    # G1-06 环境敏感性注记）。
    "from pathlib import Path;"
    "from waterprint.drafting.dxf_writer import DrawingMeta, write_dxf;"
    "from waterprint.drafting.styles import Entity, EntityGroup, base_styles;"
    "import sys;"
    "group = EntityGroup(entities=(Entity('rect', 'WP-process-pool',"
    " ((0.0, 0.0), (4.5, 3.0)), source_key='l_straight|d'),));"
    "meta = DrawingMeta(title='t', condition_key='design',"
    " repro=('h', 'e', 'd'));"
    "write_dxf(group, base_styles(), Path(sys.argv[1]), meta)"
)


def test_classes_sorted_and_crossprocess_bytes(tmp_path: Path) -> None:
    """R3 修复断言（批 14-FIX）：CLASSES 记录序==字典序+双子进程字节恒等。

    ezdxf 1.4.4 类注册序随进程熵翻转 → CLASSES 记录换位（跨进程双稳
    态，首样批缺陷②实证——进程内双跑测试不触发）→ 修复=落盘后 CLASSES
    段记录块字典序归一。未修复时注册序≠字典序必红（ezdxf 默认注册序
    非字典序）；双子进程（真跨进程）渲染字节恒等为归一后恒绿锚。
    """
    import subprocess
    import sys

    from waterprint.drafting.styles import base_styles

    local = write_dxf(_group(), base_styles(), tmp_path / "local.dxf", _meta())
    blocks = _classes_blocks(local.read_bytes())
    assert blocks == sorted(blocks)  # CLASSES 记录序==字典序（归一后）

    for i in (1, 2):  # 双子进程各渲染一份（真跨进程采样）
        subprocess.run(
            [sys.executable, "-c", _SUBPROC_SCRIPT, str(tmp_path / f"sub{i}.dxf")],
            check=True,
            capture_output=True,
        )
    first = (tmp_path / "sub1.dxf").read_bytes()
    second = (tmp_path / "sub2.dxf").read_bytes()
    assert first == second  # 跨进程字节恒等（CLASSES 双稳态已归一）
    assert _classes_blocks(first) == sorted(_classes_blocks(first))


def test_classes_ezdxf_channel_crosscheck(tmp_path: Path) -> None:
    """R 轮 G1-01 补强：ezdxf readfile 独立通道交叉验证 CLASSES 解析。

    测试辅助 _classes_blocks 与实现解析器同构（同错同绿风险——双审
    G1-01）：本用例经 ezdxf 自身解析器（readfile 后 classes.classes
    OrderedDict 键序=文件序）交叉验证名集合与序一致，解析规格不依赖
    自写单侧。
    """
    import ezdxf

    from waterprint.drafting.styles import base_styles

    out = write_dxf(_group(), base_styles(), tmp_path / "cross.dxf", _meta())
    names = [key[0] for key in ezdxf.readfile(out).classes.classes]
    from_blocks = [
        block[3].decode("utf-8") for block in _classes_blocks(out.read_bytes())
    ]
    assert sorted(from_blocks) == sorted(names)  # 名集合经独立通道一致
    assert from_blocks == names  # 序一致（ezdxf 键序=文件序=归一字典序）


def test_sort_classes_malformed_failclosed(tmp_path: Path) -> None:
    """R 轮 G1-03 补强：畸形输入（缺段/配对破缺）fail-closed 实证。

    构造不经解析器（bytes 子串定位）：段名破坏=缺段面；段体内行界
    删除=组码-值配对破缺面——两形态均须抛 InvalidDrawingError。
    """
    from waterprint.drafting.dxf_writer import InvalidDrawingError
    from waterprint.drafting.styles import base_styles

    sort_classes = getattr(_mod, "_sort_classes_section")
    good = write_dxf(_group(), base_styles(), tmp_path / "good.dxf", _meta())
    data = good.read_bytes()

    bare = tmp_path / "bare.dxf"  # 缺段形态：段头名破坏（字面量唯一出现）
    bare.write_bytes(data.replace(b"\r\nCLASSES\r\n", b"\r\nCLASSXS\r\n", 1))
    with pytest.raises(InvalidDrawingError):
        sort_classes(bare)

    head = data.index(b"\r\nCLASSES\r\n")
    first_class = data.index(b"\r\nCLASS\r\n", head)  # 段体内首记录行
    cut = data.index(b"\r\n", first_class + len(b"\r\nCLASS"))
    broken = tmp_path / "broken.dxf"  # 配对破缺：删一行界=两行并一（奇）
    broken.write_bytes(data[:cut] + data[cut + 2:])
    with pytest.raises(InvalidDrawingError):
        sort_classes(broken)


def test_sort_classes_lf_line_ending_platform(tmp_path: Path) -> None:
    """CI 首验回修（批 14-FIX 热修）：LF 行尾（Linux ezdxf 导出原生形态）
    归一不误拒——行尾自适应防再发（Windows 本地单平台盲区补强）。"""
    sort_classes = getattr(_mod, "_sort_classes_section")
    from waterprint.drafting.styles import base_styles

    good = write_dxf(_group(), base_styles(), tmp_path / "crlf.dxf", _meta())
    lf = tmp_path / "lf.dxf"
    lf.write_bytes(good.read_bytes().replace(b"\r\n", b"\n"))
    sort_classes(lf)  # LF 形态归一不抛（CI Linux 实红形态）
    normalized = lf.read_bytes()
    assert b"\r\n" not in normalized  # 写回保持 LF 原生形态
    # LF 归一结果与 CRLF 归一结果仅行尾异（段内容/序一致）
    assert normalized.replace(b"\n", b"\r\n") == good.read_bytes()

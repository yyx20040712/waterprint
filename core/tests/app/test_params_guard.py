"""params_guard 镜像测试：方案参数四面守护（批3b 拆件随迁——flows/params_guard.py）。

输入:  waterprint.flows 公开符号（再导出面零变——经包正门断言）+ golden 数据
输出:  守护契约断言（四面清单式逐条判定+builtin 带 A-1~A-3——先红后绿承载件）
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint.flows")


def test_flows_reexport_contract() -> None:
    """门一 N8：再导出契约——flows 包正门可导入 params_guard 且可调用
    （拆件后模块名/函数名占用钉死——镜像测试导入面零变的事实锚）。"""
    from waterprint.flows import params_guard as reexported

    assert callable(reexported)
    assert reexported is _mod.params_guard  # 同一函数对象（真再导出非复制）


def _load_municipal(golden_data_dir: Path):
    """golden municipal 项目装载（load_project 正门——test_flows 同款）。"""
    from waterprint.app import load_project

    return load_project(golden_data_dir / "municipal_34760" / "input_project.json")


def _catalog_params(unit_id: str):
    """目录参数面（discover_units——32 包 manifest）。"""
    from waterprint.app import discover_units

    return discover_units()[unit_id][0].params


def _first_grid_entry(specs: dict) -> tuple[str, float]:
    """首个 grid 声明参数（档位首档值——cass n_pool 等枚举维）。"""
    for field_id, spec in specs.items():
        if spec.grid:
            return field_id, float(spec.grid[0])
    raise AssertionError("municipal_aao 无 grid 参数（目录面漂移——查 manifest）")


def test_params_guard_accepts_known_finite_on_grid(golden_data_dir: Path) -> None:
    """guard 面①②③全过：已知键+有限值+命中档位=accepted 全绿。"""
    project = _load_municipal(golden_data_dir)
    specs = {p.field_id: p for p in _catalog_params("municipal_aao")}
    grid_key, grid_value = _first_grid_entry(specs)
    verdicts = _mod.params_guard(project, "municipal_aao", {grid_key: grid_value})
    assert len(verdicts) == 1
    assert verdicts[0].accepted is True
    assert verdicts[0].reason is None
    assert verdicts[0].key == grid_key


def test_params_guard_rejects_each_face(golden_data_dir: Path) -> None:
    """guard 三面逐条拒（清单式不拒整批——CLI/MCP 共用口径）。"""
    project = _load_municipal(golden_data_dir)
    specs = {p.field_id: p for p in _catalog_params("municipal_aao")}
    grid_key, grid_value = _first_grid_entry(specs)
    off = grid_value + 1.0  # 档位外（相邻整数必不在档——枚举维离散）
    while off in {float(g) for g in specs[grid_key].grid}:
        off += 1.0
    verdicts = _mod.params_guard(
        project,
        "municipal_aao",
        {
            "ghost_key_never": 3,  # ②键未知
            grid_key: off,  # ③档位外
            "ns": True,  # ①bool 冒充 int（已知键——值面独立命中）
        },
    )
    table = {v.key: v for v in verdicts}
    assert table["ghost_key_never"].accepted is False
    assert "不在" in (table["ghost_key_never"].reason or "")
    assert table[grid_key].accepted is False
    assert "档位" in (table[grid_key].reason or "")
    assert table["ns"].accepted is False
    assert "数值" in (table["ns"].reason or "")


def test_params_guard_string_value_rejected(golden_data_dir: Path) -> None:
    """guard ①面独立证：str 值逐条拒（AUDIT2 C-4 探针场景）。"""
    project = _load_municipal(golden_data_dir)
    specs = {p.field_id: p for p in _catalog_params("municipal_aao")}
    grid_key, grid_value = _first_grid_entry(specs)
    verdicts = _mod.params_guard(
        project, "municipal_aao", {grid_key: "垃圾字符串值"}
    )
    assert verdicts[0].accepted is False
    assert "数值" in (verdicts[0].reason or "")


def test_params_guard_builtin_kind_channel(golden_data_dir: Path) -> None:
    """guard kind 通道：node 含 kind→builtin 参数面（inlet.kz 与 server 版同径）。"""
    project = _load_municipal(golden_data_dir)
    verdicts = _mod.params_guard(project, "inlet", {"kz": 1.5})
    assert len(verdicts) == 1 and verdicts[0].accepted is True
    unknown = _mod.params_guard(project, "inlet", {"ghost_builtin_key": 1.5})
    assert unknown[0].accepted is False


def test_params_guard_unknown_unit_and_node(golden_data_dir: Path) -> None:
    """guard 守护前置：unit_id 不在 nodes / catalog 目录外→InvalidFlowError。"""
    project = _load_municipal(golden_data_dir)
    with pytest.raises(_mod.InvalidFlowError, match="design.nodes"):
        _mod.params_guard(project, "ghost_unit", {"any": 1.0})
    stranger = project.model_copy(
        update={
            "design": project.design.model_copy(
                update={
                    "nodes": {
                        **project.design.nodes,
                        "not_in_catalog": {},  # 无 kind 且不在注册表
                    }
                }
            )
        }
    )
    with pytest.raises(_mod.InvalidFlowError, match="目录"):
        _mod.params_guard(stranger, "not_in_catalog", {"any": 1.0})


# ── face④/builtin 带（批3b——b3a §二 A/E 组+§七追认 2026-09-26）──────────


def test_params_guard_face4_rejects_out_of_band(golden_data_dir: Path) -> None:
    """批3b face④：spec.range 闭区间执法——越带拒（audit §一「range 声明后
    无人执法」收口；specs 来自 discover_units 目录=天然全量覆盖）。"""
    project = _load_municipal(golden_data_dir)
    verdicts = _mod.params_guard(
        project, "municipal_aao", {"ns": 0.2, "t_p": 0.5, "h2": 5.5}
    )
    table = {v.key: v for v in verdicts}
    assert table["ns"].accepted is False  # 0.2 越上界（ns 带 [0.05, 0.15]）
    assert "越带" in (table["ns"].reason or "")
    assert table["t_p"].accepted is False  # 0.5 越下界（厌氧 HRT 带 [1.0, 2.0]）
    assert "越带" in (table["t_p"].reason or "")
    assert table["h2"].accepted is True  # 带内（5.5 ∈ [4.0, 6.0]）放行
    assert table["h2"].reason is None and table["h2"].warn is None  # 常规面零提示


def test_params_guard_face4_closed_band_edges_accepted(golden_data_dir: Path) -> None:
    """批3b face④：闭区间含端点——带缘值放行（[min,max] 闭区间语义）。"""
    project = _load_municipal(golden_data_dir)
    verdicts = _mod.params_guard(project, "municipal_aao", {"ns": 0.05, "t_p": 2.0})
    assert all(v.accepted for v in verdicts)
    assert all(v.warn is None for v in verdicts)  # warn 默认 None（向后兼容面）


def test_params_guard_face4_cass_t_draw_band(golden_data_dir: Path) -> None:
    """批3b D-5 执法验证：cass t_draw range [1.0,1.5]——2.0 越带拒、1.2 带内
    收、双端点 1.0/1.5 闭区间接受（GB §7.6.36 排水时间——唯一 range 新声明
    的 face④ 接线实证）。"""
    project = _load_municipal(golden_data_dir)
    cass = project.model_copy(
        update={
            "design": project.design.model_copy(
                update={"nodes": {**project.design.nodes, "municipal_cass": {}}}
            )
        }
    )
    bad = _mod.params_guard(cass, "municipal_cass", {"t_draw": 2.0})
    assert bad[0].accepted is False
    assert "1.5" in (bad[0].reason or "")  # 带上界进拒因文案
    for edge in (1.0, 1.5):  # 闭区间双端点接受（门一 N4——含端点语义独立证）
        good = _mod.params_guard(cass, "municipal_cass", {"t_draw": edge})
        assert good[0].accepted is True, edge
    interior = _mod.params_guard(cass, "municipal_cass", {"t_draw": 1.2})
    assert interior[0].accepted is True and interior[0].warn is None


def test_params_guard_builtin_q_band_rejects(golden_data_dir: Path) -> None:
    """批3b A-1/A-3：q_avg_daily 硬界——≤0 或 >60 m³/s（=518.4 万 m³/d 顶格
    类上界）拒收；60.0 恰界放行（闭上界——518.4e4×parse 因子二进制精确）。"""
    project = _load_municipal(golden_data_dir)
    from waterprint.flows.params_guard import _Q_REJECT_MAX_M3S

    assert _Q_REJECT_MAX_M3S == 60.0  # 门一 N1：换算链精确钉（防 parse 多步 1ulp 漂移）
    for bad_value in (0.0, -3.0, 61.0, 34760.7):  # 末项=audit AUD-B3 病例
        verdict = _mod.params_guard(project, "inlet", {"q_avg_daily": bad_value})
        assert verdict[0].accepted is False, bad_value
        assert "硬界" in (verdict[0].reason or "")
        assert verdict[0].warn is None  # 拒收不带提示
    on_edge = _mod.params_guard(project, "inlet", {"q_avg_daily": 60.0})
    assert on_edge[0].accepted is True  # 闭上界：恰 60 不拒（严格 > 才拒）
    assert "超大型厂" in (on_edge[0].warn or "")  # 同时落 A-2 提示带（=518.4 万 m³/d）
    golden_scale = _mod.params_guard(project, "inlet", {"q_avg_daily": 0.402315})
    assert golden_scale[0].accepted is True  # 3.476 万 m³/d=常规量级零提示


def test_params_guard_builtin_q_band_warns_without_blocking(golden_data_dir: Path) -> None:
    """批3b A-2/A-3：提示带不阻塞——(0,10 m³/d) 小流量与 >100 万 m³/d 超大型
    厂 accepted=True+warn 文案（E2E-1 软提示面：硬错早拒、软提示不拦）。"""
    project = _load_municipal(golden_data_dir)
    small = _mod.params_guard(project, "inlet", {"q_avg_daily": 1e-5})  # =0.864 m³/d
    assert small[0].accepted is True
    assert small[0].reason is None
    assert "下限" in (small[0].warn or "")
    large = _mod.params_guard(project, "inlet", {"q_avg_daily": 12.0})  # ≈103.7 万 m³/d
    assert large[0].accepted is True
    assert large[0].reason is None
    assert "超大型厂——请复核规模口径（万 m³/d vs m³/s）与池数分格" in (
        large[0].warn or ""
    )
    # kz 不设带（b3a E 组尾——现行无来源留待手册原册，如实登记）
    kz = _mod.params_guard(project, "inlet", {"kz": 1.5})
    assert kz[0].accepted is True and kz[0].warn is None

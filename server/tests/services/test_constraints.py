"""constraints 服务镜像测试：kb 装载投影/fail-visible/确定性（CP1 D4~D7）。

输入:  waterprint_server.services.constraints 公开符号+真源 kb（仓库 data 面）
输出:  服务契约断言（41 条六类/装载守卫四路/缓存单例/双跑字节同）
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint_server.services.constraints")
list_constraints = getattr(_mod, "ConstraintCatalog") and getattr(_mod, "list_constraints")

pytestmark = [
    pytest.mark.skipif(
        list_constraints is None,
        reason="实现未就绪：waterprint_server.services.constraints（CP1）",
    ),
    pytest.mark.anyio,
]

# 真源 kb 面（仓库 data 目录——conftest REPO_DATA 同源推导）
_REPO = Path(__file__).resolve().parents[3] / "data"  # server/tests/services/→仓库根

# kb 计数分 kind 形态（RATIFY-L4 1.3.0：spacing_check 2 已追认；SPC2 1.4.0：
# boundary_check 1；批3b 1.5.0：geometry_guard 8——b3a-research.md §二 B 组+
# §七追认 2026-09-26 追认单直录——增删同步；margin-kb-20261001 1.6.0
# 双侧带 5 条→1.6.1 已追认定稿〔Ruling 2026-10-01 pending §32 销账〕
# ——_DRAFT16_KEYS 起草键集随批撤除+五键 expression 全锁面补齐；
# 1A1 批 1.7.0：input_band 7 条〔Kz 带+进水六指标上限带——§1a1 起草表〕）
_FILTER_COUNT = 11
_EFFLUENT_COUNT = 12
_SPACING_COUNT = 2
_BOUNDARY_COUNT = 1
_GEOMETRY_COUNT = 8
_INPUT_BAND_COUNT = 7
# 1.7.0 起草态七键（1A1 批——§1a1 清单待追认；追认单直录无 factor 源键，
# 手册原册页级复核归追认批；追认后随标记回写撤集——_DRAFT16 先例形态）
_DRAFT17_KEYS = {
    "inlet.kz_band",
    "inlet.quality_upper.cod", "inlet.quality_upper.bod5",
    "inlet.quality_upper.ss", "inlet.quality_upper.nh3n",
    "inlet.quality_upper.tn", "inlet.quality_upper.tp",
}


def test_catalog_projects_kb_truth() -> None:
    """R1 真源投影：41 条六类+key 唯一+声明序（kb 声明面恰等钳制）。"""
    catalog = list_constraints(_REPO)
    entries = catalog.entries
    assert len(entries) == (
        _FILTER_COUNT
        + _EFFLUENT_COUNT
        + _SPACING_COUNT
        + _BOUNDARY_COUNT
        + _GEOMETRY_COUNT
        + _INPUT_BAND_COUNT
    )
    kinds = [e.kind for e in entries]
    assert kinds.count("enumeration_filter") == _FILTER_COUNT
    assert kinds.count("effluent_standard") == _EFFLUENT_COUNT
    assert kinds.count("spacing_check") == _SPACING_COUNT
    assert kinds.count("boundary_check") == _BOUNDARY_COUNT
    assert kinds.count("geometry_guard") == _GEOMETRY_COUNT
    assert kinds.count("input_band") == _INPUT_BAND_COUNT
    keys = [e.key for e in entries]
    assert len(set(keys)) == len(keys)  # key 唯一（README 硬规则）
    raw = json.loads((_REPO / "constraint_kb" / "constraints.json").read_bytes())
    assert keys == [str(item["key"]) for item in raw["entries"]]  # 声明序逐字


def test_filter_entries_carry_unit_kinds_and_values() -> None:
    """R1/D2：过滤条目 unit_kinds 非空+expression 含行字段与数值投影。"""
    catalog = list_constraints(_REPO)
    filters = [e for e in catalog.entries if e.kind == "enumeration_filter"]
    assert all(e.unit_kinds for e in filters)  # 过滤面必绑单元
    # Ruling 2026-08-31 全部追认——过滤/出水两类标记已回写（RATIFY-L4 后
    # spacing 亦已追认——分 kind 断言形态维持，禁全库一刀切）
    # 1.6.1 定稿（Ruling 2026-10-01）：1.6.0 扩 5 条标记已回写——全量断言
    # 恢复无过滤形态（_DRAFT16_KEYS 起草键集撤除）
    ratified = [
        e for e in catalog.entries if e.kind in {"enumeration_filter", "effluent_standard"}
    ]
    assert all("已追认" in e.value_basis for e in ratified)
    by_key = {e.key: e for e in filters}
    assert by_key["vxinglvchi.v_filter_band"].expression == (
        "v_filter_act >= 7.0 and v_filter_act <= 10.0"
    )
    assert by_key["vxinglvchi.v_forced_band"].expression == "v_forced_act <= 13.0"
    assert by_key["nongsuo.solid_load_band"].unit_kinds == ("sludge_nongsuo",)
    # 1.6.0 双侧带五键全锁面（margin 产出面——bilateral band_of 形态；
    # 1.6.1 追认批补齐全五键 expression+unit_kinds——门一 d1 复审 N-2 兑现）
    assert by_key["aao.hrt_anoxic_band"].expression == (
        "t_n >= 2.0 and t_n <= 4.0"
    )
    assert by_key["aao.sludge_age_band"].expression == (
        "theta_c >= 11.0 and theta_c <= 23.0"
    )
    assert by_key["cass.sludge_age_band"].expression == (
        "theta_c >= 15.0 and theta_c <= 25.0"
    )
    assert by_key["cass.draw_band"].expression == (
        "h_draw >= 1.0 and h_draw <= 2.0"
    )
    assert by_key["cass.ns_act_band"].expression == (
        "ns_act >= 0.05 and ns_act <= 0.15"
    )
    for _k in ("aao.hrt_anoxic_band", "aao.sludge_age_band"):
        assert by_key[_k].unit_kinds == ("municipal_aao",)
    for _k in ("cass.sludge_age_band", "cass.draw_band", "cass.ns_act_band"):
        assert by_key[_k].unit_kinds == ("municipal_cass",)


def test_effluent_entries_not_offered_for_filtering() -> None:
    """D2：出水参考面 unit_kinds 恒空（picker 不供选——机制事实面）。"""
    catalog = list_constraints(_REPO)
    effluent = [e for e in catalog.entries if e.kind == "effluent_standard"]
    assert len(effluent) == _EFFLUENT_COUNT
    assert all(e.unit_kinds == () for e in effluent)
    assert any("GB 18918-2002" in e.source for e in effluent)


def test_spacing_entries_carry_threshold_contract() -> None:
    """L4b：spacing_check 面契约——expression 形态 `min_clearance_m >= <float>`
    （server services.site 唯一解析面——README 钉面）+通用/限定对双形态+起草态。
    """
    import re

    catalog = list_constraints(_REPO)
    spacing = [e for e in catalog.entries if e.kind == "spacing_check"]
    assert len(spacing) == _SPACING_COUNT
    pattern = re.compile(r"^min_clearance_m >= [0-9]+(?:\.[0-9]+)?$")
    assert all(pattern.match(e.expression) for e in spacing)
    # ①通用全对：unit_kinds 空=全对通用（装配面 None 语义）；②限定对两键
    general = next(e for e in spacing if e.key == "site.clearance_general")
    assert general.unit_kinds == () and general.severity == "WARN"
    scoped = next(e for e in spacing if e.key == "site.clearance_nongsuo_xiaohua")
    assert set(scoped.unit_kinds) == {"sludge_nongsuo", "sludge_xiaohua"}
    assert scoped.severity == "ERROR"
    # 数值权威=已追认（Ruling 2026-09-03——manifest 1.3.0 同面）
    assert all("已追认" in e.value_basis for e in spacing)


def test_boundary_entry_carry_containment_contract() -> None:
    """SPC2：boundary_check 面契约——expression 形态 `containment == inside`
    （server services.site 唯一 severity 解析面——README 钉面）+全构筑物+
    ERROR 起草待专家确认态（kb 1.4.0——数据策略 v2）。
    """
    catalog = list_constraints(_REPO)
    boundary = [e for e in catalog.entries if e.kind == "boundary_check"]
    assert len(boundary) == _BOUNDARY_COUNT
    entry = boundary[0]
    assert entry.key == "site.boundary_containment"
    assert entry.expression == "containment == inside"
    assert entry.unit_kinds == ()  # 全构筑物（不设限定面）
    assert entry.severity == "ERROR"
    # 起草态口径：工程惯例类比+待专家确认（未追认——pending-domain-expert 登记）
    assert "待专家确认" in entry.source
    assert "待专家确认" in entry.value_basis


def test_geometry_entries_carry_domain_gates() -> None:
    """批3b：geometry_guard 面契约——四量（l_pool/b_pool/v_pool/n_aerator）
    各提示/拒收双门（expression 单侧 `field <= <float>`——真=门内合规，
    B1 勘正后与 enumeration_filter 极性统一）+unit_kinds 恒 AAO/CASS 双键
    +severity WARN/ERROR 分层+数值权威=追认单直录（b3a-research.md §二 B 组
    +§七 2026-09-26——无 coefficients 源键）。
    """
    catalog = list_constraints(_REPO)
    geometry = [e for e in catalog.entries if e.kind == "geometry_guard"]
    assert len(geometry) == _GEOMETRY_COUNT
    by_key = {e.key: e for e in geometry}
    assert set(by_key) == {
        "geometry.l_pool_hint", "geometry.l_pool_reject",
        "geometry.b_pool_hint", "geometry.b_pool_reject",
        "geometry.v_pool_hint", "geometry.v_pool_reject",
        "geometry.n_aerator_hint", "geometry.n_aerator_reject",
    }
    for entry in geometry:  # 门内合规单侧式（越门=假被滤——勾选即过滤越门行）
        field = entry.key.split(".")[1].rsplit("_", 1)[0]
        assert entry.expression.startswith(f"{field} <= ")
        assert set(entry.unit_kinds) == {"municipal_aao", "municipal_cass"}
    for suffix, severity in (("hint", "WARN"), ("reject", "ERROR")):
        matches = [e for e in geometry if e.key.endswith(f"_{suffix}")]
        assert len(matches) == 4  # 四量各一提示门一拒收门
        assert all(e.severity == severity for e in matches)
    # 门位=b3a 追认单直录（kb 首次无 coefficients 源键形态——数值权威=追认单）
    assert all("b3a-research.md" in e.value_basis for e in geometry)
    assert all("追认 2026-09-26" in e.value_basis for e in geometry)
    assert by_key["geometry.l_pool_hint"].expression == "l_pool <= 300.0"
    assert by_key["geometry.l_pool_reject"].expression == "l_pool <= 1000.0"
    assert by_key["geometry.b_pool_hint"].expression == "b_pool <= 100.0"
    assert by_key["geometry.b_pool_reject"].expression == "b_pool <= 400.0"
    assert by_key["geometry.v_pool_hint"].expression == "v_pool <= 150000.0"
    assert by_key["geometry.v_pool_reject"].expression == "v_pool <= 1500000.0"
    assert by_key["geometry.n_aerator_hint"].expression == "n_aerator <= 50000.0"
    assert by_key["geometry.n_aerator_reject"].expression == "n_aerator <= 1000000.0"


def test_input_band_entries_carry_inlet_reasonableness_contract() -> None:
    """1A1：input_band 面契约——Kz 静态合理性带（全表包络，流量分档精确表
    挂账）+进水六指标浓度上限带（expression `field <= <float>` 单侧上界式，
    字段=契约既有进水面命名 kz/BOD5/CODCR/SS/NH3N/TN/TP 非新建）；横切
    进水面非单元包（unit_kinds 恒空=全适用——boundary_check 空表先例）；
    severity 全 WARN（逐条定级归 1A6）；起草态=追认单直录（无 coefficients
    源键——geometry_guard 先例；手册原册页级复核归追认批）。
    """
    catalog = list_constraints(_REPO)
    bands = [e for e in catalog.entries if e.kind == "input_band"]
    assert len(bands) == _INPUT_BAND_COUNT
    by_key = {e.key: e for e in bands}
    assert set(by_key) == _DRAFT17_KEYS
    # 表达式锁面（起草表七条逐字——数值漂移即红）
    assert by_key["inlet.kz_band"].expression == "kz >= 1.3 and kz <= 2.7"
    assert by_key["inlet.quality_upper.cod"].expression == "CODCR <= 1000.0"
    assert by_key["inlet.quality_upper.bod5"].expression == "BOD5 <= 400.0"
    assert by_key["inlet.quality_upper.ss"].expression == "SS <= 400.0"
    assert by_key["inlet.quality_upper.nh3n"].expression == "NH3N <= 50.0"
    assert by_key["inlet.quality_upper.tn"].expression == "TN <= 60.0"
    assert by_key["inlet.quality_upper.tp"].expression == "TP <= 10.0"
    for entry in bands:  # 横切进水面：空表=全适用+WARN+起草态标记在册
        assert entry.unit_kinds == ()
        assert entry.severity == "WARN"
        assert "起草待追认" in entry.value_basis
        assert "追认单直录" in entry.value_basis
    # Kz 带挂账注记在册（流量相关精确内插表显式挂账不录——预裁决③）
    assert "挂账" in by_key["inlet.kz_band"].value_basis


def test_filter_values_match_factors_truth() -> None:
    """R2（DS-03）：过滤条目数值=coefficients factors.yaml 同值自动对照。

    从真源读 band 值重组表达式断言——系数库升版漂移即红（kb README
    「数值不另立权威」纪律的机器钳制）。
    """
    import re

    factors_text = (_REPO / "coefficients" / "factors.yaml").read_text(encoding="utf-8")
    values: dict[str, float] = {}
    pattern = re.compile(
        r'- key: "factor\.([a-z_0-9.]+)"\s*\n\s*value: ([0-9.]+)'
    )
    for match in pattern.finditer(factors_text):
        values[f"factor.{match.group(1)}"] = float(match.group(2))

    def band_expression(prefix: str, field: str) -> str:
        return f"{field} >= {values[f'{prefix}.min']} and {field} <= {values[f'{prefix}.max']}"

    catalog = list_constraints(_REPO)
    by_key = {e.key: e for e in catalog.entries}
    assert by_key["vxinglvchi.v_filter_band"].expression == band_expression(
        "factor.vxinglvchi.v_filter_band", "v_filter_act"
    )
    assert by_key["ganhua.moisture_out_band"].expression == band_expression(
        "factor.ganhua.moisture_out_band", "p_out"
    )
    assert by_key["nongsuo.solid_load_band"].expression == band_expression(
        "factor.nongsuo.solid_load_band", "q_solid_act"
    )
    assert by_key["xiaohua.vs_load_band"].expression == band_expression(
        "factor.xiaohua.vs_load_band", "l_vs"
    )
    assert (
        by_key["vxinglvchi.v_forced_band"].expression
        == f"v_forced_act <= {values['factor.vxinglvchi.v_forced_band.max']}"
    )
    assert by_key["nongsuo.moisture_out_band"].expression == band_expression(
        "factor.nongsuo.moisture_out_band", "p_out"
    )


def test_missing_kb_fails_visible(tmp_path: Path) -> None:
    """R2：kb 缺失=RuntimeError 显式拒（禁静默空表）。"""
    with pytest.raises(RuntimeError, match="未就绪"):
        list_constraints(tmp_path)


def test_corrupt_kb_fails_visible(tmp_path: Path) -> None:
    """R2：损坏 JSON/形态非法=RuntimeError（fail-visible）。"""
    kb_dir = tmp_path / "constraint_kb"
    kb_dir.mkdir()
    (kb_dir / "constraints.json").write_bytes(b"{not json")
    with pytest.raises(RuntimeError, match="损坏"):
        list_constraints(tmp_path)
    (kb_dir / "constraints.json").write_bytes(json.dumps({"entries": "nope"}).encode())
    with pytest.raises(RuntimeError, match="形态非法"):
        list_constraints(tmp_path)


def test_bad_entry_fails_visible(tmp_path: Path) -> None:
    """R2：条目缺键/key 重复/kind 越界=RuntimeError（库级完整性拒）。"""
    kb_dir = tmp_path / "constraint_kb"
    kb_dir.mkdir()

    def _write(entries: list[dict]) -> None:  # type: ignore[type-arg]
        (kb_dir / "constraints.json").write_bytes(
            (json.dumps({"entries": entries}, ensure_ascii=False) + "\n").encode("utf-8")
        )

    good = {
        "key": "t.a", "kind": "enumeration_filter", "unit_kinds": ["x"],
        "label": "t", "expression": "f >= 1.0", "source": "GB t；待追认",
        "severity": "WARN", "value_basis": "t——AI 起草待追认",
    }
    _write([{k: v for k, v in good.items() if k != "source"}])
    with pytest.raises(RuntimeError, match="缺键"):
        list_constraints(tmp_path)
    _write([dict(good), dict(good)])
    with pytest.raises(RuntimeError, match="重复"):
        list_constraints(tmp_path)
    bad_kind = dict(good, key="t.b", kind="hard")
    _write([bad_kind])
    with pytest.raises(RuntimeError, match="kind 越界"):
        list_constraints(tmp_path)
    # R2（DS-04/06/08）：severity 越界+空串 key+unit_kinds 型检三路
    _write([dict(good, key="t.c", severity="hard")])
    with pytest.raises(RuntimeError, match="severity 越界"):
        list_constraints(tmp_path)
    _write([dict(good, key="")])
    with pytest.raises(RuntimeError, match="非空"):
        list_constraints(tmp_path)
    _write([dict(good, key="t.d", unit_kinds="x")])
    with pytest.raises(RuntimeError, match="unit_kinds"):
        list_constraints(tmp_path)


def test_cache_singleton_and_determinism() -> None:
    """R3+R2（DS-05）：同路径单例（is 同）+清缓存重装载字节同。"""
    first = list_constraints(_REPO)
    second = list_constraints(_REPO)
    assert first is second  # 路径键缓存单例
    a = first.model_dump_json()
    _mod._load.cache_clear()  # noqa: SLF001  # 测试面私有访问（真重装载对比——DS-05）
    reloaded = list_constraints(_REPO)
    assert reloaded is not first
    assert reloaded.model_dump_json() == a  # 重装载字节同


@pytest.mark.anyio
async def test_constraints_endpoint_shape(client) -> None:  # type: ignore[no-untyped-def]
    """D4：GET /api/constraints 200——41 条六类（client 面=路由+装配全链）。"""
    response = await client.get("/api/constraints")
    assert response.status_code == 200
    payload = response.json()
    entries = payload["entries"]
    assert len(entries) == (
        _FILTER_COUNT
        + _EFFLUENT_COUNT
        + _SPACING_COUNT
        + _BOUNDARY_COUNT
        + _GEOMETRY_COUNT
        + _INPUT_BAND_COUNT
    )
    assert {e["kind"] for e in entries} == {
        "enumeration_filter", "effluent_standard", "spacing_check",
        "boundary_check", "geometry_guard", "input_band",
    }
    first_filter = next(e for e in entries if e["kind"] == "enumeration_filter")
    assert set(first_filter.keys()) == {
        "key", "kind", "unit_kinds", "label", "expression",
        "source", "severity", "value_basis",
    }

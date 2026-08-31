"""constraints 服务镜像测试：kb 装载投影/fail-visible/确定性（CP1 D4~D7）。

输入:  waterprint_server.services.constraints 公开符号+真源 kb（仓库 data 面）
输出:  服务契约断言（18 条两类/装载守卫四路/缓存单例/双跑字节同）
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

# kb 1.0.0 起草态计数（追认升版时同步——manifest.yaml 版本记录同面）
_FILTER_COUNT = 6
_EFFLUENT_COUNT = 12


def test_catalog_projects_kb_truth() -> None:
    """R1 真源投影：18 条两类+key 唯一+声明序（kb 声明面恰等钳制）。"""
    catalog = list_constraints(_REPO)
    entries = catalog.entries
    assert len(entries) == _FILTER_COUNT + _EFFLUENT_COUNT
    kinds = [e.kind for e in entries]
    assert kinds.count("enumeration_filter") == _FILTER_COUNT
    assert kinds.count("effluent_standard") == _EFFLUENT_COUNT
    keys = [e.key for e in entries]
    assert len(set(keys)) == len(keys)  # key 唯一（README 硬规则）
    raw = json.loads((_REPO / "constraint_kb" / "constraints.json").read_bytes())
    assert keys == [str(item["key"]) for item in raw["entries"]]  # 声明序逐字


def test_filter_entries_carry_unit_kinds_and_values() -> None:
    """R1/D2：过滤条目 unit_kinds 非空+expression 含行字段与数值投影。"""
    catalog = list_constraints(_REPO)
    filters = [e for e in catalog.entries if e.kind == "enumeration_filter"]
    assert all(e.unit_kinds for e in filters)  # 过滤面必绑单元
    assert all("待追认" in e.value_basis for e in catalog.entries)  # 醒目标注逐条
    by_key = {e.key: e for e in filters}
    assert by_key["vxinglvchi.v_filter_band"].expression == (
        "v_filter_act >= 7.0 and v_filter_act <= 10.0"
    )
    assert by_key["vxinglvchi.v_forced_band"].expression == "v_forced_act <= 13.0"
    assert by_key["nongsuo.solid_load_band"].unit_kinds == ("sludge_nongsuo",)


def test_effluent_entries_not_offered_for_filtering() -> None:
    """D2：出水参考面 unit_kinds 恒空（picker 不供选——机制事实面）。"""
    catalog = list_constraints(_REPO)
    effluent = [e for e in catalog.entries if e.kind == "effluent_standard"]
    assert len(effluent) == _EFFLUENT_COUNT
    assert all(e.unit_kinds == () for e in effluent)
    assert any("GB 18918-2002" in e.source for e in effluent)


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


def test_cache_singleton_and_determinism() -> None:
    """R3：同路径单例（is 同）+双跑字节同（sort_keys）。"""
    first = list_constraints(_REPO)
    second = list_constraints(_REPO)
    assert first is second  # 路径键缓存单例
    a = first.model_dump_json()
    b = second.model_dump_json()
    assert a == b


@pytest.mark.anyio
async def test_constraints_endpoint_shape(client) -> None:  # type: ignore[no-untyped-def]
    """D4：GET /api/constraints 200——18 条两类（client 面=路由+装配全链）。"""
    response = await client.get("/api/constraints")
    assert response.status_code == 200
    payload = response.json()
    entries = payload["entries"]
    assert len(entries) == _FILTER_COUNT + _EFFLUENT_COUNT
    assert {e["kind"] for e in entries} == {"enumeration_filter", "effluent_standard"}
    first_filter = next(e for e in entries if e["kind"] == "enumeration_filter")
    assert set(first_filter.keys()) == {
        "key", "kind", "unit_kinds", "label", "expression",
        "source", "severity", "value_basis",
    }

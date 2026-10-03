"""assumptions 镜像测试：设计假设清单唯一真源（默认值显性化——病灶根治点）。

输入:  waterprint.registry.assumptions 公开符号
输出:  优先级/出处门槛/覆盖语义断言+data_version 版本声明断言（1A1 批）
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

_mod = importlib.import_module("waterprint.registry.assumptions")
Assumption = getattr(_mod, "Assumption", None)
assumption = getattr(_mod, "assumption", None)
DEFAULT_ASSUMPTIONS = getattr(_mod, "DEFAULT_ASSUMPTIONS", None)

pytestmark = pytest.mark.skipif(
    None in (Assumption, assumption, DEFAULT_ASSUMPTIONS),
    reason="实现未就绪：waterprint.registry.assumptions（M1）",
)


def test_default_assumptions_all_have_source() -> None:
    """R2：每条默认假设必须带出处（无出处不准入库）。"""
    for item in DEFAULT_ASSUMPTIONS:
        assert item.source, f"假设 {item.key} 缺出处"
        assert item.note, f"假设 {item.key} 缺影响说明"


def test_override_takes_precedence_over_default() -> None:
    """R1：项目覆盖值优先于默认值。"""
    target = DEFAULT_ASSUMPTIONS[0]
    value = assumption(target.key, {target.key: target.default + 1.0})
    assert value == pytest.approx(target.default + 1.0)


def test_unknown_key_raises() -> None:
    """未知键取值抛领域异常（禁止静默默认——魔法数借道）。"""
    with pytest.raises(Exception, match=".+"):
        assumption("no_such_assumption", {})


def test_register_without_source_rejected() -> None:
    """R2（登记侧）：无出处条目拒绝注册。"""
    with pytest.raises(Exception, match=".+"):
        Assumption(key="test_no_source", default=1.0, dim="LENGTH", source="", note="")


def test_data_version_exposed_from_manifest() -> None:
    """1A1：manifest data_version 声明→模块级版本只读暴露（装载真源直读）。

    声明值 "1.0.0"=B2-4 批数值等价搬家零升版的版本槽补声明（条目数值
    零变更）；coefficients.Coefficients.data_version 同款形态（非空 str）。
    """
    version = getattr(_mod, "DATA_VERSION")
    assert version == "1.0.0"
    manifest_text = (_mod._YAML_DATA_DIR / "manifest.yaml").read_text(  # noqa: SLF001  # 版本声明同源对账（测试面私有访问先例）
        encoding="utf-8"
    )
    assert 'data_version: "1.0.0"' in manifest_text  # 声明与暴露同源


def test_manifest_unknown_key_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """manifest 键集白名单守卫：未知键拒（data_version 扩键后仍闭门）。"""
    (tmp_path / "manifest.yaml").write_text(
        "ordered_files: [safety.yaml]\nschema_version: 1\n"
        "data_version: '1.0.0'\nbogus_key: x\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(_mod, "_YAML_DATA_DIR", tmp_path)
    with pytest.raises(_mod.InvalidAssumptionError, match="未知键"):
        _mod._load_manifest()  # noqa: SLF001  # 守卫面直调（缓存未涉及的纯函数）


def test_manifest_data_version_required_nonempty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """1A1：data_version 必在且非空 str（coefficients 同款守卫——三态拒）。"""
    cases = {
        "缺键": "ordered_files: [safety.yaml]\nschema_version: 1\n",
        "空串": "ordered_files: [safety.yaml]\nschema_version: 1\ndata_version: ''\n",
        "非 str": "ordered_files: [safety.yaml]\nschema_version: 1\ndata_version: 1.0\n",
    }
    for body in cases.values():
        (tmp_path / "manifest.yaml").write_text(body, encoding="utf-8")
        monkeypatch.setattr(_mod, "_YAML_DATA_DIR", tmp_path)
        with pytest.raises(_mod.InvalidAssumptionError, match="data_version"):
            _mod._load_manifest()  # noqa: SLF001  # 守卫面直调（缓存未涉及的纯函数）

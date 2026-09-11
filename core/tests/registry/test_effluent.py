"""registry/effluent.py 镜像测试：出水标准装载器（P2 次批 ADR-012 D6）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from waterprint.registry.effluent import (
    InvalidEffluentLoadError,
    load_effluent_standards,
)

_REPO_DATA = Path(__file__).resolve().parents[3] / "data"


def _write(tmp_path: Path, entries: list[dict[str, Any]]) -> Path:
    """constraints.json 形态测试件（entries 可含非 effluent 条目验证过滤）。"""
    file = tmp_path / "constraints.json"
    file.write_text(
        json.dumps({"comment": "test", "entries": entries}, ensure_ascii=False),
        encoding="utf-8",
    )
    return file


def _std(key: str, expression: str, label: str) -> dict[str, Any]:
    """effluent_standard 条目模板（真源形态同构）。"""
    return {"key": key, "kind": "effluent_standard", "expression": expression,
            "source": "测试", "severity": "WARN", "label": label}


def test_loads_repo_truth_data() -> None:
    """真源装载：12 条→2 标准×6 指标；限值/名称直录；字典序 a<b。"""
    standards = load_effluent_standards(
        _REPO_DATA / "constraint_kb" / "constraints.json"
    )
    assert [s.standard_id for s in standards] == [
        "gb18918.level_a", "gb18918.level_b",
    ]
    level_a = standards[0]
    assert level_a.limits == {
        "BOD5": 10.0, "CODCR": 50.0, "SS": 10.0, "NH3N": 5.0, "TN": 15.0, "TP": 0.5,
    }
    assert level_a.name_i18n == "GB 18918-2002 一级A"
    assert standards[1].limits["CODCR"] == 60.0


def test_kind_filter_and_dict_order(tmp_path: Path) -> None:
    """kind 过滤（非 effluent 条目不进标准面）+standard_id 字典序确定性。"""
    file = _write(tmp_path, [
        {"key": "spacing.x", "kind": "spacing_check", "expression": "w >= 1"},
        _std("gb.b.bod5", "BOD5_out <= 20.0", "GB B 出水 BOD5 ≤20 mg/L"),
        _std("gb.a.bod5", "BOD5_out <= 10.0", "GB A 出水 BOD5 ≤10 mg/L"),
    ])
    standards = load_effluent_standards(file)
    assert [s.standard_id for s in standards] == ["gb.a", "gb.b"]


def test_missing_file_rejected(tmp_path: Path) -> None:
    """缺文件=fail-fast（固定资产装配缺陷，禁默认回退 R3）。"""
    with pytest.raises(InvalidEffluentLoadError, match="缺失"):
        load_effluent_standards(tmp_path / "absent.json")


def test_no_effluent_entries_rejected(tmp_path: Path) -> None:
    """零 effluent 条目拒（12 条固定资产——零条即数据缺陷）。"""
    file = _write(tmp_path, [
        {"key": "spacing.x", "kind": "spacing_check", "expression": "w >= 1"},
    ])
    with pytest.raises(InvalidEffluentLoadError, match="无 kind=effluent_standard"):
        load_effluent_standards(file)


@pytest.mark.parametrize(
    ("key", "expression", "label", "message"),
    [
        ("gb.a.bod5.x", "BOD5_out <= 10.0", "N 出水 BOD5 ≤10 mg/L", "三段式"),
        ("gb.a", "BOD5_out <= 10.0", "N 出水 BOD5 ≤10 mg/L", "三段式"),
        ("gb.a.bod5", "BOD5_out < 10.0", "N 出水 BOD5 ≤10 mg/L", "受限形态"),
        ("gb.a.bod5", "bod5 <= 10.0", "N 出水 BOD5 ≤10 mg/L", "受限形态"),
        # 负限值在受限形态层即拒（正则首字符 [0-9]——负号不属限值域形态）
        ("gb.a.bod5", "BOD5_out <= -5.0", "N 出水 BOD5 ≤-5 mg/L", "受限形态"),
        ("gb.a.xyz", "XYZ_out <= 10.0", "N 出水 XYZ ≤10 mg/L", "不在 INDICATORS"),
        ("gb.a.bod5", "BOD5_out <= 0.0", "N 出水 BOD5 ≤0 mg/L", "有限且 > 0"),
        ("gb.a.bod5", "BOD5_out <= 10.0", "无分隔名段", "标准名段"),
    ],
)
def test_malformed_entries_rejected(
    tmp_path: Path, key: str, expression: str, label: str, message: str,
) -> None:
    """条目形态/域守卫逐例拒（消息含条目 key——R3 fail-fast）。"""
    file = _write(tmp_path, [_std(key, expression, label)])
    with pytest.raises(InvalidEffluentLoadError, match=message):
        load_effluent_standards(file)


def test_non_object_entry_rejected(tmp_path: Path) -> None:
    """entries 含非对象元素拒（R3 禁静默跳条——PT-N-03 A 二审真修面）。"""
    file = tmp_path / "constraints.json"
    file.write_text(
        json.dumps({
            "comment": "test",
            "entries": [
                "裸字符串条目",
                _std("gb.a.bod5", "BOD5_out <= 10.0", "GB A 出水 BOD5 ≤10 mg/L"),
            ],
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    with pytest.raises(InvalidEffluentLoadError, match="须为对象"):
        load_effluent_standards(file)


def test_inconsistent_name_segment_rejected(tmp_path: Path) -> None:
    """同 standard_id 组内 label 名段不一致拒（R2 数据格式契约）。"""
    file = _write(tmp_path, [
        _std("gb.a.bod5", "BOD5_out <= 10.0", "GB A 出水 BOD5 ≤10 mg/L"),
        _std("gb.a.ss", "SS_out <= 10.0", "GB A-改 出水 SS ≤10 mg/L"),
    ])
    with pytest.raises(InvalidEffluentLoadError, match="名段不一致"):
        load_effluent_standards(file)


def test_duplicate_indicator_rejected(tmp_path: Path) -> None:
    """重复 (standard_id, indicator) 拒（R4）。"""
    file = _write(tmp_path, [
        _std("gb.a.bod5", "BOD5_out <= 10.0", "GB A 出水 BOD5 ≤10 mg/L"),
        _std("gb.a.bod5x", "BOD5_out <= 11.0", "GB A 出水 BOD5 ≤11 mg/L"),
    ])
    # key 尾段不同但 expression 指标同——按 expression 提指标即重复
    with pytest.raises(InvalidEffluentLoadError, match="重复"):
        load_effluent_standards(file)

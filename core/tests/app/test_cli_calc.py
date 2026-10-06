"""cli_calc 镜像测试：kb 执法面 CLI 接线（kbwire-20261003）。

输入:  waterprint.cli.main（calc 子命令行为面——纯 main() 断言；
       cli_common 恒等钉归 test_cli_common.py 镜像件）
输出:  三面行为断言——①注入面（golden municipal --conditions aao →
       result.json 含 maint.municipal_aao.kb.* 恰 10 键全 1.0+
       any_fail=0.0+fixgeom.min=−1.0+双跑字节同）②宽容面（无 kb
       data_dir → UserWarning+零 kb/fixgeom 键 ratio 键在）③kb 坏档 →
       退出码 3（InvalidConstraintError 入 _CALC_VALIDATIONS 收编锚）。
"""

from __future__ import annotations

import json
import shutil
import warnings
from pathlib import Path

import pytest

from waterprint.cli import main

_REPO_ROOT = Path(__file__).resolve().parents[3]
_REPO_DATA = _REPO_ROOT / "data"


def _copy_project(golden_data_dir: Path, tmp_path: Path) -> Path:
    """golden municipal 项目拷贝（CLI 结果写面与 golden 源目录隔离）。"""
    project = golden_data_dir / "municipal_34760" / "input_project.json"
    copied = tmp_path / "proj" / "input_project.json"
    copied.parent.mkdir(parents=True)
    copied.write_bytes(project.read_bytes())
    return copied


def _data_dir_without_kb(tmp_path: Path) -> Path:
    """无 constraint_kb 的最小数据包根（coefficients 真源拷贝——env 装配面）。"""
    data_dir = tmp_path / "data"
    shutil.copytree(_REPO_DATA / "coefficients", data_dir / "coefficients")
    return data_dir


def test_cli_injects_kb_into_result(
    golden_data_dir: Path, tmp_path: Path
) -> None:
    """①注入面：calc --conditions aao → kb.* 恰 10 键全 1.0+any_fail=0.0
    +fixgeom.min=−1.0（UF-61 批 M3 探针值同源锚）+双跑 serialize 字节同。"""
    copied = _copy_project(golden_data_dir, tmp_path)
    out = tmp_path / "r.json"
    argv = ["calc", str(copied), "--conditions", "municipal_aao", "--out", str(out)]
    assert main(argv) == 0
    offline = json.loads(out.read_text(encoding="utf-8"))["summary"][
        "design_offline_municipal_aao"
    ]
    kb = {
        key: value for key, value in offline.items()
        if key.startswith("maint.municipal_aao.kb.")
        and key != "maint.municipal_aao.kb.any_fail"
    }
    assert len(kb) == 12  # geometry 8+aao 带 2+param_band 2（param.n/h2——
    # 1A4 批 dims 同名参数键合法选中全 PASS；test_app_maintenance golden 同源）
    assert set(kb.values()) == {1.0}
    assert offline["maint.municipal_aao.kb.any_fail"] == 0.0  # 全过→0.0
    assert offline["maint.municipal_aao.fixgeom.min"] == pytest.approx(-1.0)
    second = tmp_path / "r2.json"
    assert main([*argv[:-1], str(second)]) == 0
    assert out.read_bytes() == second.read_bytes()  # 双跑字节同（R3 确定性）


def test_cli_lenient_without_kb(
    golden_data_dir: Path, tmp_path: Path
) -> None:
    """②宽容面：data_dir 无 constraint_kb → UserWarning（约束知识库缺失）
    +结果零 kb/fixgeom 键（ratio 键仍在——build_standards_flow 同款宽容）。"""
    copied = _copy_project(golden_data_dir, tmp_path)
    out = tmp_path / "r.json"
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        code = main([
            "calc", str(copied), "--conditions", "municipal_aao",
            "--data-dir", str(_data_dir_without_kb(tmp_path)), "--out", str(out),
        ])
    assert code == 0
    assert any(
        issubclass(item.category, UserWarning)
        and "约束知识库缺失" in str(item.message)
        for item in caught
    )
    offline = json.loads(out.read_text(encoding="utf-8"))["summary"][
        "design_offline_municipal_aao"
    ]
    assert offline["maint.municipal_aao.ratio.n"] == pytest.approx(0.5)  # ratio 键在
    assert not any(".kb." in key or ".fixgeom." in key for key in offline)


def test_cli_bad_kb_exits_validation(
    golden_data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """③kb 坏档→退出码 3：真源 kb 拷贝后损坏一条非 effluent 条目
    （standards 装载不受扰〔kind 筛面〕），InvalidConstraintError 入
    _CALC_VALIDATIONS 读入校验族收编。"""
    copied = _copy_project(golden_data_dir, tmp_path)
    data_dir = _data_dir_without_kb(tmp_path)
    kb_dir = data_dir / "constraint_kb"
    kb_dir.mkdir()
    raw = json.loads(
        (_REPO_DATA / "constraint_kb" / "constraints.json").read_text(encoding="utf-8")
    )
    for item in raw["entries"]:
        if item["kind"] == "enumeration_filter":
            item["expression"] = "nope nonsense"  # 非法 DSL（无算符）
            break
    (kb_dir / "constraints.json").write_text(
        json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    assert main([
        "calc", str(copied), "--data-dir", str(data_dir),
        "--out", str(tmp_path / "r.json"),
    ]) == 3
    assert "校验失败" in capsys.readouterr().err


def test_cli_kb_block_exits_calculation(
    golden_data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """④kb 阻断→退出码 4（errmap E2 持久测试）：真源 155 条拷贝+追加一条
    违规 block 条目（aao design 帧 n=2 违反 n<=0——core test_run_full_calc_
    constructed_violation_raises 同源锚）→KbBlockError 入 _CALC_FAILURES
    执行期族收编→main==4+stderr 含「计算失败」与 violated key。"""
    copied = _copy_project(golden_data_dir, tmp_path)
    data_dir = _data_dir_without_kb(tmp_path)
    kb_dir = data_dir / "constraint_kb"
    kb_dir.mkdir()
    raw = json.loads(
        (_REPO_DATA / "constraint_kb" / "constraints.json").read_text(encoding="utf-8")
    )
    raw["entries"].append({
        "key": "kb.stub.cli-block",
        "kind": "geometry_guard",
        "unit_kinds": ["municipal_aao"],
        "label": "CLI 阻断退出码探针（构造越门 n<=0）",
        "expression": "n <= 0",
        "source": "测试构造（errmap E2）",
        "severity": "ERROR",
        "enforcement": "block",
        "value_basis": "测试构造",
    })
    (kb_dir / "constraints.json").write_text(
        json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    assert main([
        "calc", str(copied), "--conditions", "municipal_aao",
        "--data-dir", str(data_dir), "--out", str(tmp_path / "r.json"),
    ]) == 4
    stderr = capsys.readouterr().err
    assert "计算失败" in stderr  # _CALC_FAILURES 族消息前缀（退出码 4 面）
    assert "kb.stub.cli-block" in stderr  # violated key 透出（消息含逐条 key）


def test_calc_failures_family_real_classes_quantified() -> None:
    """errmap E2 族锚：_CALC_FAILURES 六真类绑定全量化。

    ①六真类逐一 in _CALC_FAILURES（对象同一性——类经定义模块 import，
    core 类改名→ImportError 红；改名后新类对象≠表内旧引用→同一性红）；
    ②len==6+名称集合恒等（移除/换名/加项均红——表级全量化锚）。"""
    from waterprint.cli_calc import _CALC_FAILURES
    from waterprint.contracts.manifest_validation import InvalidUnitConfig
    from waterprint.contracts.ports import InvalidConnection
    from waterprint.graph.executor_dsl import InvalidExecutionError
    from waterprint.graph.loop import LoopDivergence
    from waterprint.graph.nodes import InvalidNodeError
    from waterprint.solution.constraints import KbBlockError

    real_classes = (
        LoopDivergence, InvalidNodeError, InvalidConnection,
        InvalidUnitConfig, InvalidExecutionError, KbBlockError,
    )
    for cls in real_classes:  # tuple 成员判定=逐元素 ==（类默认==即对象同一性）
        assert cls in _CALC_FAILURES
    assert len(_CALC_FAILURES) == 6
    assert {cls.__name__ for cls in _CALC_FAILURES} == {
        cls.__name__ for cls in real_classes
    }
